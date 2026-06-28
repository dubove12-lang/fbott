import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter


class HyperliquidError(RuntimeError):
    pass


_ALL_MIDS_CACHE: Dict[str, Any] = {"ts": 0.0, "data": {}}

_HL_RATE_LOCK = threading.Lock()
_HL_LAST_REQUEST_TS = 0.0

_HTTP_SESSION = requests.Session()
_HTTP_ADAPTER = HTTPAdapter(
    pool_connections=int(os.getenv("HTTP_POOL_CONNECTIONS", "80")),
    pool_maxsize=int(os.getenv("HTTP_POOL_MAXSIZE", "160")),
    max_retries=0,
)
_HTTP_SESSION.mount("https://", _HTTP_ADAPTER)
_HTTP_SESSION.mount("http://", _HTTP_ADAPTER)


class HyperliquidClient:
    """
    Small public Hyperliquid Info API client.

    Used for enriching Hydromancer leaderboard wallet rows with live account state:
      POST https://api.hyperliquid.xyz/info
      {"type": "clearinghouseState", "user": "<wallet>"}

    This endpoint is public and does not need the Hydromancer API key.
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("HYPERLIQUID_INFO_URL", "https://api.hyperliquid.xyz/info")
        self.timeout = float(os.getenv("HYPERLIQUID_TIMEOUT", "8"))
        self.connect_timeout = float(os.getenv("HYPERLIQUID_CONNECT_TIMEOUT", "3"))
        self.read_timeout = float(os.getenv("HYPERLIQUID_READ_TIMEOUT", str(self.timeout)))

    def post_info(self, payload: Dict[str, Any]) -> Any:
        global _HL_LAST_REQUEST_TS

        max_retries = int(os.getenv("HYPERLIQUID_MAX_RETRIES", "4"))
        base_backoff = float(os.getenv("HYPERLIQUID_RETRY_BACKOFF_SECONDS", "0.75"))
        min_interval = float(os.getenv("HYPERLIQUID_MIN_REQUEST_INTERVAL_SECONDS", "0.10"))

        last_error_text = ""
        for attempt in range(max(1, max_retries + 1)):
            if min_interval > 0:
                with _HL_RATE_LOCK:
                    now = time.time()
                    wait = min_interval - (now - _HL_LAST_REQUEST_TS)
                    if wait > 0:
                        time.sleep(wait)
                    _HL_LAST_REQUEST_TS = time.time()

            try:
                response = _HTTP_SESSION.post(
                    self.base_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=(self.connect_timeout, self.read_timeout),
                )
            except requests.RequestException as exc:
                last_error_text = str(exc)
                if attempt >= max_retries:
                    raise HyperliquidError(f"Hyperliquid request failed: {exc}") from exc
                time.sleep(base_backoff * (attempt + 1))
                continue

            if response.status_code in (429, 500, 502, 503, 504):
                last_error_text = f"Hyperliquid {response.status_code}: {response.text[:500]}"
                retry_after = response.headers.get("Retry-After")
                try:
                    retry_wait = float(retry_after) if retry_after else base_backoff * (attempt + 1)
                except Exception:
                    retry_wait = base_backoff * (attempt + 1)
                if attempt < max_retries:
                    time.sleep(max(retry_wait, min_interval))
                    continue

            if response.status_code >= 400:
                raise HyperliquidError(f"Hyperliquid {response.status_code}: {response.text[:500]}")

            try:
                return response.json()
            except Exception as exc:
                raise HyperliquidError(f"Hyperliquid returned non-JSON response: {exc}") from exc

        raise HyperliquidError(last_error_text or "Hyperliquid request failed")

    def clearinghouse_state(self, user: str, dex: Optional[str] = None) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {"type": "clearinghouseState", "user": user}
        if dex:
            payload["dex"] = dex
        data = self.post_info(payload)
        return data if isinstance(data, dict) else None


    def perp_dexs(self) -> Any:
        """
        Retrieve all perpetual dexes, including HIP-3 builder-deployed perp dexes.
        """
        return self.post_info({"type": "perpDexs"})

    def all_perp_metas(self) -> Any:
        """
        Retrieve metadata for all perpetual dexes.
        """
        return self.post_info({"type": "allPerpMetas"})

    def meta(self, dex: Optional[str] = None) -> Any:
        """
        Hyperliquid perpetuals metadata for a specific perp dex.
        Default dex is the first/main perp dex.
        """
        payload: Dict[str, Any] = {"type": "meta"}
        if dex:
            payload["dex"] = dex
        return self.post_info(payload)

    def meta_and_asset_ctxs(self, dex: Optional[str] = None) -> Any:
        """
        Hyperliquid perpetuals metadata plus market contexts for a specific perp dex.
        Expected response shape: [meta, asset_ctxs].
        """
        payload: Dict[str, Any] = {"type": "metaAndAssetCtxs"}
        if dex:
            payload["dex"] = dex
        return self.post_info(payload)


    def portfolio(self, user: str) -> Any:
        """
        Hyperliquid portfolio endpoint.

        It returns period buckets such as day/week/month/allTime with
        accountValueHistory, pnlHistory, and volume where available.
        This is better for all-time vault PnL than paginating fills, because
        userFillsByTime is capped by historical fill availability.
        """
        return self.post_info({"type": "portfolio", "user": user})

    def portfolio_stats(self, user: str, window: str = "30d") -> Dict[str, Any]:
        data = self.portfolio(user)
        target = str(window or "30d").lower()
        period_map = {
            "1d": ("day", "1d"),
            "7d": ("week", "7d"),
            "30d": ("month", "30d"),
            "all": ("allTime", "all", "all_time"),
        }
        aliases = period_map.get(target)
        if not aliases:
            return {}

        bucket = None

        if isinstance(data, list):
            for item in data:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    period = str(item[0])
                    if period in aliases:
                        bucket = item[1]
                        break
                elif isinstance(item, dict):
                    period = str(item.get("period") or item.get("timeframe") or item.get("window") or "")
                    if period in aliases:
                        bucket = item
                        break

        if bucket is None and isinstance(data, dict):
            for key in aliases:
                value = data.get(key)
                if value is not None:
                    bucket = value
                    break
            if bucket is None:
                nested = data.get("data") or data.get("result")
                if isinstance(nested, dict):
                    for key in aliases:
                        value = nested.get(key)
                        if value is not None:
                            bucket = value
                            break

        if not isinstance(bucket, dict):
            return {}

        def as_float(value: Any, default: float = 0.0) -> float:
            try:
                if value is None:
                    return default
                if isinstance(value, str):
                    value = value.replace("$", "").replace(",", "").strip()
                return float(value)
            except Exception:
                return default

        pnl = None
        for key in ("pnl", "totalPnl", "total_pnl", "cumPnl", "cumulativePnl"):
            if bucket.get(key) is not None:
                pnl = as_float(bucket.get(key))
                break

        # Some portfolio payloads primarily expose pnlHistory as [timestamp, value] points.
        if pnl is None:
            pnl_history = bucket.get("pnlHistory") or bucket.get("pnl_history")
            if isinstance(pnl_history, list) and pnl_history:
                last = pnl_history[-1]
                try:
                    if isinstance(last, (list, tuple)) and len(last) >= 2:
                        pnl = as_float(last[1])
                    elif isinstance(last, dict):
                        pnl = as_float(last.get("pnl") or last.get("value") or last.get("y"))
                except Exception:
                    pass

        volume = None
        for key in ("vlm", "volume", "volumeTraded", "totalVolume", "notionalVolume"):
            if bucket.get(key) is not None:
                volume = as_float(bucket.get(key))
                break

        account_value = None
        av_history = bucket.get("accountValueHistory") or bucket.get("account_value_history")
        if isinstance(av_history, list) and av_history:
            last = av_history[-1]
            try:
                if isinstance(last, (list, tuple)) and len(last) >= 2:
                    account_value = as_float(last[1])
                elif isinstance(last, dict):
                    account_value = as_float(last.get("accountValue") or last.get("value") or last.get("y"))
            except Exception:
                pass

        return {
            "window": target,
            "portfolio_period": aliases[0],
            "pnl": pnl if pnl is not None else 0.0,
            "volume": volume if volume is not None else 0.0,
            "account_value": account_value,
            "source": "hyperliquid_portfolio",
        }


    def all_mids(self) -> Dict[str, float]:
        ttl = int(os.getenv("HYPERLIQUID_ALL_MIDS_CACHE_TTL_SECONDS", "15"))
        now = time.time()
        if _ALL_MIDS_CACHE.get("data") and (now - float(_ALL_MIDS_CACHE.get("ts", 0))) < ttl:
            return _ALL_MIDS_CACHE["data"]

        data = self.post_info({"type": "allMids"})
        if not isinstance(data, dict):
            return {}

        out: Dict[str, float] = {}
        for coin, value in data.items():
            try:
                out[str(coin)] = float(value)
            except Exception:
                continue

        _ALL_MIDS_CACHE["ts"] = now
        _ALL_MIDS_CACHE["data"] = out
        return out


    def user_fills_by_time(self, user: str, start_time: int, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "type": "userFillsByTime",
            "user": user,
            "startTime": start_time,
        }
        if end_time is not None:
            payload["endTime"] = end_time

        data = self.post_info(payload)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def _summarize_fills(self, fills: List[Dict[str, Any]], window: str = "30d") -> Dict[str, Any]:
        # De-duplicate overlapping chunk responses.
        seen = set()
        unique_fills: List[Dict[str, Any]] = []
        for fill in fills:
            key = (
                fill.get("hash"),
                fill.get("tid"),
                fill.get("time"),
                fill.get("coin"),
                fill.get("px"),
                fill.get("sz"),
                fill.get("side"),
            )
            if key in seen:
                continue
            seen.add(key)
            unique_fills.append(fill)

        volume = 0.0
        closed_pnl = 0.0
        fees = 0.0
        wins = 0
        pnl_fills = 0
        coins = set()

        for fill in unique_fills:
            try:
                px = float(fill.get("px") or fill.get("price") or 0)
                sz = float(fill.get("sz") or fill.get("size") or 0)
                volume += abs(px * sz)
            except Exception:
                pass

            try:
                fee = float(fill.get("fee") or 0)
                fees += abs(fee)
            except Exception:
                pass

            if fill.get("coin"):
                coins.add(str(fill.get("coin")))

            if fill.get("closedPnl") is not None:
                try:
                    cp = float(fill.get("closedPnl") or 0)
                    closed_pnl += cp
                    pnl_fills += 1
                    if cp > 0:
                        wins += 1
                except Exception:
                    pass

        win_rate = (wins / pnl_fills * 100) if pnl_fills else 0.0

        return {
            "window": str(window or "30d"),
            "volume": volume,
            "closed_pnl": closed_pnl,
            "fees": fees,
            "fills": len(unique_fills),
            "pnl_fills": pnl_fills,
            "win_rate": win_rate,
            "traded_pairs": sorted(coins),
        }

    def user_funding_by_time(self, user: str, start_time: int, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "type": "userFunding",
            "user": user,
            "startTime": start_time,
        }
        if end_time is not None:
            payload["endTime"] = end_time

        data = self.post_info(payload)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def user_non_funding_ledger_updates(self, user: str, start_time: int, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "type": "userNonFundingLedgerUpdates",
            "user": user,
            "startTime": start_time,
        }
        if end_time is not None:
            payload["endTime"] = end_time

        data = self.post_info(payload)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def _extract_time_ms(self, item: Dict[str, Any]) -> Optional[int]:
        for key in ("time", "timestamp", "createdAt"):
            value = item.get(key)
            if value is not None:
                try:
                    return int(value)
                except Exception:
                    pass

        nested = item.get("delta")
        if isinstance(nested, dict):
            for key in ("time", "timestamp"):
                value = nested.get(key)
                if value is not None:
                    try:
                        return int(value)
                    except Exception:
                        pass
        return None

    def user_account_age_days(self, user: str) -> int:
        """
        Best-effort account age from public Hyperliquid user activity.

        There is no simple `accountCreatedAt` in clearinghouseState. We inspect
        earliest available fills / ledger updates from a long lookback window.
        For very active wallets, this can still be an approximation because HL
        limits historical responses.
        """
        now = int(time.time() * 1000)
        # Wide lookback. If Hyperliquid does not return full history, this is still the best public approximation here.
        start = 0

        timestamps = []

        # Keep this lightweight: one call each. The heavy 30d fills path is separate and chunked.
        for fetcher in (
            lambda: self.user_fills_by_time(user=user, start_time=start, end_time=now),
            lambda: self.user_non_funding_ledger_updates(user=user, start_time=start, end_time=now),
        ):
            try:
                rows = fetcher()
                for row in rows:
                    t = self._extract_time_ms(row)
                    if t:
                        timestamps.append(t)
            except Exception:
                pass

        if not timestamps:
            return 0

        oldest = min(timestamps)
        return max(0, int((now - oldest) / (24 * 60 * 60 * 1000)))

    def user_30d_funding_stats(self, user: str, window: str = "30d") -> Dict[str, Any]:
        end_time = int(time.time() * 1000)
        start_time = self._window_start_ms(window)

        # Split into chunks for better coverage and lower chance of hitting per-response caps.
        chunks = int(os.getenv("HYPERLIQUID_FUNDING_CHUNKS", "5"))
        chunks = max(1, min(5, chunks))
        chunk_ms = max(1, (end_time - start_time) // chunks)

        windows = []
        for i in range(chunks):
            s = start_time + i * chunk_ms
            e = end_time if i == chunks - 1 else start_time + (i + 1) * chunk_ms - 1
            windows.append((s, e))

        rows: List[Dict[str, Any]] = []
        max_workers = max(1, min(chunks, int(os.getenv("HYPERLIQUID_FUNDING_WORKERS", str(chunks)))))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.user_funding_by_time, user=user, start_time=s, end_time=e) for s, e in windows]
            for future in as_completed(futures):
                try:
                    rows.extend(future.result())
                except Exception:
                    pass

        # De-duplicate
        seen = set()
        unique_rows = []
        for row in rows:
            key = (
                row.get("time"),
                row.get("coin") or (row.get("delta") or {}).get("coin") if isinstance(row.get("delta"), dict) else None,
                str(row.get("delta")),
            )
            if key in seen:
                continue
            seen.add(key)
            unique_rows.append(row)

        total_funding = 0.0
        coins = set()
        for row in unique_rows:
            candidates = []

            for key in ("usdc", "funding", "fundingPayment", "amount", "pnl"):
                if row.get(key) is not None:
                    candidates.append(row.get(key))

            delta = row.get("delta")
            if isinstance(delta, dict):
                for key in ("usdc", "funding", "fundingPayment", "amount", "pnl"):
                    if delta.get(key) is not None:
                        candidates.append(delta.get(key))
                if delta.get("coin"):
                    coins.add(str(delta.get("coin")))

            if row.get("coin"):
                coins.add(str(row.get("coin")))

            for value in candidates[:1]:
                try:
                    total_funding += float(value)
                except Exception:
                    pass

        return {
            "window": str(window or "30d"),
            "total_funding": total_funding,
            "funding_events": len(unique_rows),
            "funding_coins": sorted(coins),
            "funding_chunks": chunks,
        }

    def _window_start_ms(self, window: str) -> int:
        end_time = int(time.time() * 1000)
        normalized = str(window or "30d").lower()
        days_by_window = {
            "1d": 1,
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "all": 3650,
        }
        days = days_by_window.get(normalized, 30)
        return end_time - days * 24 * 60 * 60 * 1000

    def user_30d_fill_stats(self, user: str, window: str = "30d") -> Dict[str, Any]:
        """
        Hyperliquid caps userFillsByTime at 2,000 fills per response and only the
        10,000 most recent fills are available. To improve coverage, split the
        last 30 days into 5 time windows and fetch them in parallel:
          5 windows x 2,000 fills = up to 10,000 fills.
        """
        end_time = int(time.time() * 1000)
        start_time = self._window_start_ms(window)

        chunks = int(os.getenv("HYPERLIQUID_FILLS_CHUNKS", "5"))
        chunks = max(1, min(5, chunks))
        chunk_ms = max(1, (end_time - start_time) // chunks)

        windows = []
        for i in range(chunks):
            s = start_time + i * chunk_ms
            e = end_time if i == chunks - 1 else start_time + (i + 1) * chunk_ms - 1
            windows.append((s, e))

        max_workers = int(os.getenv("HYPERLIQUID_FILLS_WORKERS", str(chunks)))
        max_workers = max(1, min(chunks, max_workers))

        all_fills: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.user_fills_by_time, user=user, start_time=s, end_time=e)
                for s, e in windows
            ]
            for future in as_completed(futures):
                try:
                    all_fills.extend(future.result())
                except Exception:
                    # Keep other windows usable if one chunk fails.
                    pass

        stats = self._summarize_fills(all_fills, window=window)
        stats["chunks"] = chunks
        stats["max_possible_fills"] = chunks * 2000
        stats["is_probably_capped"] = stats["fills"] >= chunks * 2000
        return stats

