import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from typing import Any, Dict, List, Optional
from .database import get_db, row_to_dict, rows_to_dicts
from .hydromancer_client import HydromancerClient, HydromancerError, normalize_leaderboard_row
from .hyperliquid_client import HyperliquidClient, HyperliquidError
from .token_icons import get_token_icon_url

FATBOT_DEFAULT_VAULTS = [
    "0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A",
    "0x20c4F93BcAd80C7B83c20dEcA8A7bc91B9e6a3b0",
]

_FATBOT_VAULT_CACHE: Dict[str, Any] = {"ts": 0.0, "data": []}
_FATBOT_VAULT_CACHE_TTL_SECONDS = int(os.getenv("FATBOT_VAULT_CACHE_TTL_SECONDS", "60"))

_TRADER_LEADERBOARD_CACHE: Dict[str, Any] = {"ts": 0.0, "data": []}
_TRADER_LEADERBOARD_CACHE_TTL_SECONDS = int(os.getenv("TRADER_LEADERBOARD_CACHE_TTL_SECONDS", "60"))
_PROFILE_CACHE: Dict[str, Any] = {}
_PROFILE_CACHE_TTL_SECONDS = int(os.getenv("PROFILE_CACHE_TTL_SECONDS", "120"))




def make_wallet_address() -> str:
    prefix = ''.join(random.choice('0123456789ABCDEF') for _ in range(4))
    suffix = ''.join(random.choice('0123456789ABCDEF') for _ in range(4))
    return f"0xCOPY{prefix}...{suffix}"



def hydromancer_enabled() -> bool:
    return HydromancerClient().enabled



def _profile_cache_get(key: str) -> Optional[Dict[str, Any]]:
    item = _PROFILE_CACHE.get(str(key).lower())
    if not item:
        return None
    if (time.time() - float(item.get("ts", 0))) > _PROFILE_CACHE_TTL_SECONDS:
        return None
    return item.get("data")


def _profile_cache_set(key: str, data: Dict[str, Any]) -> Dict[str, Any]:
    _PROFILE_CACHE[str(key).lower()] = {"ts": time.time(), "data": data}
    return data



def _normalize_leaderboard_filters(
    window: str = "30d",
    sort_by: str = "totalPnl",
    limit: int = 50,
    min_trades: int = 0,
    min_days_active: int = 0,
) -> Dict[str, Any]:
    valid_windows = {"1d", "7d", "30d", "90d", "all"}
    valid_sort = {"totalPnl", "volume", "winRate"}

    window = str(window or "30d").lower()
    if window not in valid_windows:
        window = "30d"

    sort_by = str(sort_by or "totalPnl")
    if sort_by not in valid_sort:
        sort_by = "totalPnl"

    try:
        limit = int(limit)
    except Exception:
        limit = 50
    limit = max(1, min(200, limit))

    try:
        min_trades = int(min_trades)
    except Exception:
        min_trades = 0
    min_trades = max(0, min_trades)

    try:
        min_days_active = int(min_days_active)
    except Exception:
        min_days_active = 0
    min_days_active = max(0, min_days_active)

    return {
        "window": window,
        "sort_by": sort_by,
        "limit": limit,
        "min_trades": min_trades,
        "min_days_active": min_days_active,
    }


def _leaderboard_cache_key(prefix: str, filters: Dict[str, Any]) -> str:
    return "|".join([
        prefix,
        str(filters.get("window")),
        str(filters.get("sort_by")),
        str(filters.get("limit")),
        str(filters.get("min_trades")),
        str(filters.get("min_days_active")),
    ])


def _apply_local_leaderboard_filters(rows: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    min_trades = int(filters.get("min_trades") or 0)
    min_days = int(filters.get("min_days_active") or 0)
    limit = int(filters.get("limit") or 50)
    sort_by = str(filters.get("sort_by") or "totalPnl")

    filtered = []
    for row in rows:
        trades = int(row.get("total_trades") or row.get("trades") or 0)
        days = int(row.get("days_active") or row.get("account_age_days") or 0)
        if trades < min_trades:
            continue
        if days < min_days:
            continue
        filtered.append(row)

    def sort_value(row: Dict[str, Any]) -> float:
        if sort_by == "volume":
            return float(row.get("volume") or row.get("volume_traded") or 0)
        if sort_by == "winRate":
            return float(row.get("win_rate") or 0)
        return float(row.get("total_pnl") or row.get("pnl_usd") or row.get("pnl_pct") or 0)

    filtered.sort(key=sort_value, reverse=True)
    return filtered[:limit]

def get_trader_source() -> str:
    return "hydromancer" if hydromancer_enabled() else "sqlite_mock"


def get_summary() -> Dict[str, Any]:
    with get_db() as db:
        trader_count = db.execute("SELECT COUNT(*) c FROM smart_traders").fetchone()["c"]
        wallet_count = db.execute("SELECT COUNT(*) c FROM copy_wallets").fetchone()["c"]
        active_wallets = db.execute("SELECT COUNT(*) c FROM copy_wallets WHERE status = 'active'").fetchone()["c"]
        total_value = db.execute("SELECT COALESCE(SUM(value),0) v FROM copy_wallets").fetchone()["v"]
        total_pnl = db.execute("SELECT COALESCE(SUM(total_pnl),0) p FROM copy_wallets").fetchone()["p"]
        avg_drift = db.execute("SELECT COALESCE(AVG(drift),0) d FROM copy_wallets").fetchone()["d"]
        return {
            "listed_traders": trader_count,
            "copy_wallets": wallet_count,
            "active_wallets": active_wallets,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "avg_drift": avg_drift,
            "trader_source": get_trader_source(),
        }



def _enrich_top_traders_with_current_exposure(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Lightweight current exposure enrichment for Hydromancer Top Traders rows.

    Hydromancer leaderboard gives PnL/volume/win-rate stats, but it does not
    provide current long/short exposure. For that, we fetch Hyperliquid
    clearinghouseState per wallet and compute exposure from open positions.

    This is capped and cached through the leaderboard cache to avoid making the
    Top Traders tab too slow.
    """
    enabled = os.getenv("TOP_TRADERS_EXPOSURE_ENRICH", "true").lower() in ("1", "true", "yes", "on")
    if not enabled or not rows:
        return rows

    try:
        enrich_limit = int(os.getenv("TOP_TRADERS_EXPOSURE_ENRICH_LIMIT", "50"))
    except Exception:
        enrich_limit = 50
    enrich_limit = max(0, min(enrich_limit, len(rows)))

    try:
        workers = int(os.getenv("TOP_TRADERS_EXPOSURE_WORKERS", "12"))
    except Exception:
        workers = 12
    workers = max(1, min(workers, max(1, enrich_limit)))

    def enrich_one(item: Dict[str, Any]) -> Dict[str, Any]:
        address = str(item.get("address") or "")
        if not address:
            return item

        try:
            hl_client = HyperliquidClient()
            hl_state = hl_client.clearinghouse_state(address)
            if hl_state:
                item["hl_state_status"] = "ok"
                item["account_value"] = _extract_account_value_from_state(hl_state) or item.get("account_value", 0)
                if not item.get("account_value"):
                    item["account_value"] = _account_value_from_portfolio_fallback(hl_client, address, "30d")
                    if item.get("account_value"):
                        item["account_value_source"] = "hyperliquid_portfolio"
                # For exposure, positionValue from clearinghouseState is enough;
                # allMids is not needed, keeping this path much faster.
                item["positions"] = _extract_positions_from_state(hl_state, all_mids={})
                item["open_positions"] = len(item["positions"])
                item["margin_summary"] = hl_state.get("marginSummary") or hl_state.get("crossMarginSummary") or {}
                item = _attach_current_exposure_metrics(item)
        except Exception as exc:
            item["hl_state_status"] = f"exposure_error: {exc}"

        return item

    head = rows[:enrich_limit]
    tail = rows[enrich_limit:]

    enriched: List[Optional[Dict[str, Any]]] = [None] * len(head)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(enrich_one, dict(row)): idx for idx, row in enumerate(head)}
        for future, idx in []:
            pass
        for future in future_map:
            idx = future_map[future]
            try:
                enriched[idx] = future.result()
            except Exception:
                enriched[idx] = head[idx]

    return [row if row is not None else head[i] for i, row in enumerate(enriched)] + tail


def list_traders(
    force_refresh: bool = False,
    window: str = "30d",
    sort_by: str = "totalPnl",
    limit: int = 50,
    min_trades: int = 0,
    min_days_active: int = 0,
) -> List[Dict[str, Any]]:
    filters = _normalize_leaderboard_filters(window, sort_by, limit, min_trades, min_days_active)
    cache_key = _leaderboard_cache_key("traders", filters)

    now = time.time()
    cached = _TRADER_LEADERBOARD_CACHE.get(cache_key)
    if (not force_refresh) and cached and (now - float(cached.get("ts", 0))) < _TRADER_LEADERBOARD_CACHE_TTL_SECONDS:
        return cached["data"]

    client = HydromancerClient()
    if client.enabled:
        try:
            rows = client.user_pnl_leaderboard(
                window=filters["window"],
                sort_by=filters["sort_by"],
                limit=filters["limit"],
                min_trades=filters["min_trades"],
                min_days_active=filters["min_days_active"],
            )
            normalized = [normalize_leaderboard_row(row, idx + 1) for idx, row in enumerate(rows)]
            normalized = [row for row in normalized if row.get("address")]
            if not normalized:
                raise HydromancerError("Hydromancer userPnlLeaderboard returned zero usable rows")

            for idx, row in enumerate(normalized, start=1):
                row["rank"] = idx
                row["leaderboard_window"] = filters["window"]
                row["leaderboard_sort_by"] = filters["sort_by"]

            normalized = _enrich_top_traders_with_current_exposure(normalized)

            _TRADER_LEADERBOARD_CACHE[cache_key] = {"ts": now, "data": normalized}
            return normalized
        except HydromancerError as exc:
            print(f"[Hydromancer] leaderboard failed: {exc}")
            allow_fallback = os.getenv("HYDROMANCER_ALLOW_MOCK_FALLBACK", "false").lower() in ("1", "true", "yes", "on")
            if not allow_fallback:
                raise

    with get_db() as db:
        data = rows_to_dicts(db.execute("SELECT * FROM smart_traders ORDER BY score DESC").fetchall())
        for row in data:
            row["source"] = "sqlite_mock"

        data = _apply_local_leaderboard_filters(data, filters)
        _TRADER_LEADERBOARD_CACHE[cache_key] = {"ts": now, "data": data}
        return data


def hydromancer_check() -> Dict[str, Any]:
    client = HydromancerClient()
    if not client.enabled:
        return {
            "enabled": False,
            "ok": False,
            "source": "missing_api_key",
            "message": "HYDROMANCER_API_KEY is not set",
            "rows": 0,
        }

    rows = client.user_pnl_leaderboard(
        window=os.getenv("HYDROMANCER_LEADERBOARD_WINDOW", "30d"),
        sort_by=os.getenv("HYDROMANCER_LEADERBOARD_SORT_BY", "totalPnl"),
        limit=min(int(os.getenv("HYDROMANCER_LEADERBOARD_LIMIT", "50")), 5),
        min_trades=int(os.getenv("HYDROMANCER_LEADERBOARD_MIN_TRADES", "0")),
        min_days_active=int(os.getenv("HYDROMANCER_LEADERBOARD_MIN_DAYS_ACTIVE", "0")),
    )
    normalized = [normalize_leaderboard_row(row, idx + 1) for idx, row in enumerate(rows)]
    return {
        "enabled": True,
        "ok": True,
        "source": "hydromancer",
        "rows": len(normalized),
        "supported_windows": ["1d", "7d", "30d", "90d", "all"],
        "supported_sort_by": ["totalPnl", "volume", "winRate"],
        "sample": normalized[:3],
    }



def _fatbot_vault_addresses() -> List[str]:
    raw = os.getenv("FATBOT_VAULT_ADDRESSES", "").strip()
    if raw:
        values = [x.strip() for x in raw.split(",") if x.strip()]
        if values:
            return values
    return FATBOT_DEFAULT_VAULTS


def _enrich_with_hyperliquid_live_stats(row: Dict[str, Any], address: str, window: str = "30d") -> Dict[str, Any]:
    """
    Compose vault/trader live stats from public Hyperliquid endpoints.

    v43 speed-up:
    - clearinghouseState, allMids, 30d fills, 30d funding, and account age are launched concurrently.
    - allMids has its own short cache in HyperliquidClient.
    - results are still cached by list_fatbot_vaults/profile cache.
    """
    try:
        hl_client = HyperliquidClient()

        with ThreadPoolExecutor(max_workers=5) as executor:
            f_state = executor.submit(hl_client.clearinghouse_state, address)
            f_mids = executor.submit(hl_client.all_mids)
            f_fills = executor.submit(hl_client.user_30d_fill_stats, address, window)
            use_portfolio_stats = str(window or "30d").lower() in ("1d", "7d", "30d", "all")
            f_portfolio = executor.submit(hl_client.portfolio_stats, address, window) if use_portfolio_stats else None
            f_funding = executor.submit(hl_client.user_30d_funding_stats, address, window)
            f_age = executor.submit(hl_client.user_account_age_days, address)

            hl_state = None
            all_mids = {}
            try:
                hl_state = f_state.result()
            except Exception as exc:
                row["hl_state_status"] = f"error: {exc}"

            try:
                all_mids = f_mids.result()
            except Exception:
                all_mids = {}

            if hl_state:
                row["account_value"] = _extract_account_value_from_state(hl_state) or row.get("account_value", 0)
                if not row.get("account_value"):
                    row["account_value"] = _account_value_from_portfolio_fallback(hl_client, address, window)
                    if row.get("account_value"):
                        row["account_value_source"] = "hyperliquid_portfolio"
                row["positions"] = _extract_positions_from_state(hl_state, all_mids=all_mids)
                row["open_positions"] = len(row["positions"])
                row["margin_summary"] = hl_state.get("marginSummary") or hl_state.get("crossMarginSummary") or {}
                row = _attach_current_exposure_metrics(row)

            try:
                fill_stats = f_fills.result()
                row["total_pnl"] = fill_stats.get("closed_pnl", row.get("total_pnl", 0))
                row["pnl_30d"] = row["total_pnl"]
                row["pnl_90d"] = row["total_pnl"]
                row["volume"] = fill_stats.get("volume", row.get("volume", 0))
                row["volume_traded"] = row["volume"]
                row["total_fees"] = fill_stats.get("fees", row.get("total_fees", 0))
                row["fees"] = row["total_fees"]
                row["trades"] = fill_stats.get("fills", row.get("trades", 0))
                row["total_trades"] = row["trades"]
                row["win_rate"] = fill_stats.get("win_rate", row.get("win_rate", 0))
                row["traded_pairs"] = fill_stats.get("traded_pairs", row.get("traded_pairs", []))
                row["traded_pairs_count"] = len(row["traded_pairs"])
                row["stats_window"] = str(window or "30d").lower()
                row["fills_chunks"] = fill_stats.get("chunks", 1)
                row["fills_max_possible"] = fill_stats.get("max_possible_fills", 2000)
                row["fills_is_probably_capped"] = fill_stats.get("is_probably_capped", False)
            except Exception as exc:
                row["fills_status"] = f"error: {exc}"

            # Prefer Hyperliquid portfolio stats for supported windows, especially all-time.
            # This avoids treating capped fills as full all-time history.
            if f_portfolio is not None:
                try:
                    portfolio_stats = f_portfolio.result()
                    if portfolio_stats:
                        row["portfolio_stats_source"] = portfolio_stats.get("source")
                        row["portfolio_period"] = portfolio_stats.get("portfolio_period")
                        row["total_pnl"] = portfolio_stats.get("pnl", row.get("total_pnl", 0))
                        row["pnl_usd"] = row["total_pnl"]
                        row["pnl_source"] = "hyperliquid_portfolio"
                        if portfolio_stats.get("volume") is not None:
                            row["volume"] = portfolio_stats.get("volume", row.get("volume", 0))
                            row["volume_traded"] = row["volume"]
                        if portfolio_stats.get("account_value") is not None and portfolio_stats.get("account_value") != 0:
                            row["account_value"] = portfolio_stats.get("account_value")
                except Exception as exc:
                    row["portfolio_status"] = f"error: {exc}"

            try:
                funding_stats = f_funding.result()
                row["total_funding"] = funding_stats.get("total_funding", row.get("total_funding", 0))
                row["funding"] = row["total_funding"]
                row["funding_events"] = funding_stats.get("funding_events", 0)
                row["funding_coins"] = funding_stats.get("funding_coins", [])
            except Exception as exc:
                row["funding_status"] = f"error: {exc}"

            try:
                row["account_age_days"] = f_age.result()
            except Exception as exc:
                row["account_age_status"] = f"error: {exc}"

        account_value = float(row.get("account_value") or 0)
        total_pnl = float(row.get("total_pnl") or 0)
        row["pnl_pct"] = (total_pnl / account_value * 100) if account_value else 0.0
        row["pnl_30d"] = row["pnl_pct"]
        row["pnl_90d"] = row["pnl_pct"]
        row["pnl_display_mode"] = "percent_of_account_value"
        row["pnl_usd"] = total_pnl

        row["hl_state_status"] = row.get("hl_state_status", "ok")
    except Exception as exc:
        row["hl_state_status"] = f"error: {exc}"
        row.setdefault("positions", [])
        row.setdefault("open_positions", 0)
        row.setdefault("pnl_pct", 0.0)
        row.setdefault("pnl_display_mode", "percent_of_account_value")
        row.setdefault("pnl_usd", float(row.get("total_pnl") or 0))
        row.setdefault("long_notional", 0.0)
        row.setdefault("short_notional", 0.0)
        row.setdefault("gross_notional", 0.0)
        row.setdefault("net_notional", 0.0)
        row.setdefault("gross_exposure", 0.0)
        row.setdefault("gross_exposure_pct", 0.0)
        row.setdefault("net_exposure", 0.0)
        row.setdefault("net_exposure_pct", 0.0)
        row.setdefault("long_exposure_share_pct", 0.0)
        row.setdefault("short_exposure_share_pct", 0.0)

    return row



def list_fatbot_vaults(
    force_refresh: bool = False,
    window: str = "30d",
    sort_by: str = "totalPnl",
    limit: int = 50,
    min_trades: int = 0,
    min_days_active: int = 0,
) -> List[Dict[str, Any]]:
    """
    Platform-created/fixed FatBot vault leaderboard.

    The same UI filters are accepted for FatBot Vaults:
    - window controls the HL fills/funding lookback used to compose PnL/volume/funding.
    - sort/min filters are applied locally after vault stats are composed.
    """
    filters = _normalize_leaderboard_filters(window, sort_by, limit, min_trades, min_days_active)
    cache_key = _leaderboard_cache_key("fatbot_vaults", filters)

    now = time.time()
    cached = _FATBOT_VAULT_CACHE.get(cache_key)
    if (not force_refresh) and cached and (now - float(cached.get("ts", 0))) < _FATBOT_VAULT_CACHE_TTL_SECONDS:
        return cached["data"]

    addresses = _fatbot_vault_addresses()
    out: List[Dict[str, Any]] = []

    for idx, address in enumerate(addresses, start=1):
        base = {
            "vault_id": f"fatbot-vault-{idx}",
            "address": address,
            "label": f"FatBot Vault #{idx}",
            "source": "fatbot_vault",
            "rank": idx,
            "is_fatbot_vault": True,
            "total_pnl": 0,
            "volume": 0,
            "volume_traded": 0,
            "win_rate": 0,
            "trades": 0,
            "total_trades": 0,
            "days_active": 0,
            "account_age_days": 0,
            "total_funding": 0,
            "positions": [],
            "open_positions": 0,
            "leaderboard_window": filters["window"],
            "leaderboard_sort_by": filters["sort_by"],
        }

        base = _enrich_with_hyperliquid_live_stats(base, address, window=filters["window"])
        out.append(base)

    out = _apply_local_leaderboard_filters(out, filters)
    for idx, row in enumerate(out, start=1):
        row["rank"] = idx

    _FATBOT_VAULT_CACHE[cache_key] = {"ts": now, "data": out}
    return out


def get_trader(
    address: str,
    window: str = "30d",
    sort_by: str = "totalPnl",
    limit: int = 50,
    min_trades: int = 0,
    min_days_active: int = 0,
) -> Optional[Dict[str, Any]]:
    filters = _normalize_leaderboard_filters(window, sort_by, limit, min_trades, min_days_active)
    profile_cache_key = _leaderboard_cache_key(f"profile:{address.lower()}", filters)

    cached_profile = _profile_cache_get(profile_cache_key)
    if cached_profile is not None:
        return cached_profile

    # FatBot vault profiles are platform vaults, even when the address also appears in external leaderboards.
    for vault in list_fatbot_vaults(
        window=filters["window"],
        sort_by=filters["sort_by"],
        limit=filters["limit"],
        min_trades=0,
        min_days_active=0,
    ):
        if str(vault.get("address", "")).lower() == address.lower() or str(vault.get("vault_id", "")) == address:
            vault["history"] = []
            return _profile_cache_set(profile_cache_key, vault)

    with get_db() as db:
        trader = row_to_dict(db.execute("SELECT * FROM smart_traders WHERE address = ?", (address,)).fetchone())
        if trader:
            trader["positions"] = rows_to_dicts(
                db.execute("SELECT coin, side, notional, entry, mark, pnl, pnl_pct, leverage, liq_price FROM trader_positions WHERE trader_address = ?", (address,)).fetchall()
            )
            trader["history"] = [
                {"label": "Jan", "value": 82}, {"label": "Feb", "value": 89}, {"label": "Mar", "value": 91},
                {"label": "Apr", "value": 98}, {"label": "May", "value": 112}, {"label": "Jun", "value": 119},
                {"label": "Jul", "value": 123}, {"label": "Aug", "value": 131}, {"label": "Sep", "value": 138},
                {"label": "Oct", "value": 149}, {"label": "Nov", "value": 164}, {"label": "Dec", "value": 171},
            ]
            trader["source"] = "sqlite_mock"
            return trader

    # Hydromancer leaderboard rows are not stored in SQLite by default.
    # Find the address in the live leaderboard and enrich it with public Hyperliquid live state.
    client = HydromancerClient()
    if client.enabled:
        for t in list_traders(
        window=filters["window"],
        sort_by=filters["sort_by"],
        limit=filters["limit"],
        min_trades=filters["min_trades"],
        min_days_active=filters["min_days_active"],
    ):
            if str(t.get("address", "")).lower() == address.lower():
                t["positions"] = []
                t["history"] = []
                t["hl_state_status"] = "not_loaded"

                try:
                    hl_client = HyperliquidClient()
                    hl_state = hl_client.clearinghouse_state(address)
                    all_mids = {}
                    try:
                        all_mids = hl_client.all_mids()
                    except Exception:
                        all_mids = {}

                    if hl_state:
                        t["hl_state_status"] = "ok"
                        t["account_value"] = _extract_account_value_from_state(hl_state) or t.get("account_value", 0)
                        if not t.get("account_value"):
                            t["account_value"] = _account_value_from_portfolio_fallback(hl_client, address, filters["window"])
                            if t.get("account_value"):
                                t["account_value_source"] = "hyperliquid_portfolio"
                        t["positions"] = _extract_positions_from_state(hl_state, all_mids=all_mids)
                        t["open_positions"] = len(t["positions"])
                        t["margin_summary"] = hl_state.get("marginSummary") or hl_state.get("crossMarginSummary") or {}
                        t = _attach_current_exposure_metrics(t)
                except Exception as exc:
                    # Do not fail trader profile just because the live state enrichment failed.
                    t["hl_state_status"] = f"error: {exc}"

                if not t.get("account_value"):
                    try:
                        fallback_hl_client = HyperliquidClient()
                        t["account_value"] = _account_value_from_portfolio_fallback(fallback_hl_client, address, filters["window"])
                        if t.get("account_value"):
                            t["account_value_source"] = "hyperliquid_portfolio"
                    except Exception:
                        pass

                return _profile_cache_set(profile_cache_key, t)

    for vault in list_fatbot_vaults(
        window=filters["window"],
        sort_by=filters["sort_by"],
        limit=filters["limit"],
        min_trades=0,
        min_days_active=0,
    ):
        if str(vault.get("address", "")).lower() == address.lower() or str(vault.get("vault_id", "")) == address:
            vault["history"] = []
            return _profile_cache_set(profile_cache_key, vault)

    return None


def _extract_account_value_from_state(state: Dict[str, Any]) -> float:
    margin = state.get("marginSummary") or state.get("crossMarginSummary") or {}
    return float(margin.get("accountValue") or margin.get("totalRawUsd") or 0)


def _account_value_from_portfolio_fallback(hl_client: HyperliquidClient, address: str, window: str = "30d") -> float:
    """
    Fallback account value source for wallets that have no open perp positions.

    clearinghouseState should usually expose marginSummary.accountValue even with
    zero positions, but some accounts/API states can return no useful value.
    portfolio accountValueHistory is a good fallback for display.
    """
    for candidate_window in (window, "30d", "all"):
        try:
            stats = hl_client.portfolio_stats(address, candidate_window)
            value = float(stats.get("account_value") or 0) if stats else 0.0
            if value:
                return value
        except Exception:
            pass
    return 0.0


def _attach_current_exposure_metrics(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Current exposure metrics from live open positions.

    long_notional = sum current notional of Long positions
    short_notional = sum current notional of Short positions
    gross_exposure = (long_notional + short_notional) / account_value
    net_exposure = (long_notional - short_notional) / account_value
    long_exposure_share_pct / short_exposure_share_pct = side share of total gross open exposure
    """
    positions = row.get("positions") or []
    account_value = float(row.get("account_value") or 0)

    long_notional = 0.0
    short_notional = 0.0

    for pos in positions:
        try:
            notional = abs(float(pos.get("notional") or 0))
        except Exception:
            notional = 0.0

        side = str(pos.get("side") or "").lower()
        if "short" in side:
            short_notional += notional
        else:
            long_notional += notional

    gross_notional = long_notional + short_notional
    net_notional = long_notional - short_notional

    row["long_notional"] = long_notional
    row["short_notional"] = short_notional
    row["gross_notional"] = gross_notional
    row["net_notional"] = net_notional

    row["gross_exposure"] = (gross_notional / account_value) if account_value else 0.0
    row["gross_exposure_pct"] = row["gross_exposure"] * 100
    row["net_exposure"] = (net_notional / account_value) if account_value else 0.0
    row["net_exposure_pct"] = row["net_exposure"] * 100

    row["long_exposure_share_pct"] = (long_notional / gross_notional * 100) if gross_notional else 0.0
    row["short_exposure_share_pct"] = (short_notional / gross_notional * 100) if gross_notional else 0.0

    # Compatibility names for existing UI/schema.
    row["long_exposure_pct"] = row["long_exposure_share_pct"]
    row["short_exposure_pct"] = row["short_exposure_share_pct"]

    return row


def _extract_positions_from_state(state: Dict[str, Any], all_mids: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
    rows = []
    asset_positions = state.get("assetPositions") or state.get("positions") or []
    all_mids = all_mids or {}

    for item in asset_positions:
        pos = item.get("position") if isinstance(item, dict) and "position" in item else item
        if not isinstance(pos, dict):
            continue

        coin = pos.get("coin") or pos.get("asset") or "?"
        szi = float(pos.get("szi") or pos.get("size") or 0)
        if szi == 0:
            continue

        entry = float(pos.get("entryPx") or pos.get("entry") or 0)

        # Current account notional from HL state
        position_value = float(pos.get("positionValue") or pos.get("notional") or 0)

        # Raw prices sometimes present directly in clearinghouseState
        mark_raw = pos.get("markPx") or pos.get("mark") or pos.get("oraclePx") or pos.get("midPx")
        derived_mark = float(mark_raw or 0)

        # Fallback derived mark from current notional / abs(size)
        if derived_mark == 0 and position_value and abs(szi) > 0:
            derived_mark = position_value / abs(szi)

        # Preferred live price source = Hyperliquid allMids
        live_price = 0.0
        if coin in all_mids:
            try:
                live_price = float(all_mids[coin])
            except Exception:
                live_price = 0.0

        # Final price used for display / rough pnl%
        price_for_display = live_price or derived_mark

        notional = abs(position_value or (szi * price_for_display if price_for_display else 0))
        pnl = float(pos.get("unrealizedPnl") or pos.get("pnl") or 0)

        leverage_obj = pos.get("leverage")
        if isinstance(leverage_obj, dict):
            leverage = float(leverage_obj.get("value") or 0)
        else:
            leverage = float(leverage_obj or 0)

        liq_raw = pos.get("liquidationPx") or pos.get("liqPx") or 0
        liq_price = float(liq_raw or 0)

        pnl_pct = 0
        if entry and abs(szi) > 0 and price_for_display:
            if szi > 0:
                pnl_pct = ((price_for_display - entry) / entry) * 100
            else:
                pnl_pct = ((entry - price_for_display) / entry) * 100

        rows.append({
            "coin": coin,
            "icon_url": get_token_icon_url(coin),
            "side": "Long" if szi > 0 else "Short",
            "notional": notional,
            "size": abs(szi),
            "entry": entry,
            "mark": derived_mark,
            "live_price": live_price,
            "display_price": price_for_display,
            "price_source": "allMids" if live_price else ("clearinghouseState" if derived_mark else "unknown"),
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "leverage": leverage,
            "liq_price": liq_price,
        })

    return rows


def list_wallets() -> List[Dict[str, Any]]:
    with get_db() as db:
        wallets = rows_to_dicts(db.execute("SELECT * FROM copy_wallets ORDER BY id DESC").fetchall())
        for w in wallets:
            w["settings"] = row_to_dict(db.execute("SELECT * FROM copy_wallet_settings WHERE wallet_id = ?", (w["id"],)).fetchone())
            w["positions"] = rows_to_dicts(db.execute("SELECT * FROM copy_wallet_positions WHERE wallet_id = ?", (w["id"],)).fetchall())
        return wallets


def get_wallet(wallet_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as db:
        wallet = row_to_dict(db.execute("SELECT * FROM copy_wallets WHERE id = ?", (wallet_id,)).fetchone())
        if not wallet:
            return None
        wallet["settings"] = row_to_dict(db.execute("SELECT * FROM copy_wallet_settings WHERE wallet_id = ?", (wallet_id,)).fetchone())
        wallet["positions"] = rows_to_dicts(db.execute("SELECT * FROM copy_wallet_positions WHERE wallet_id = ?", (wallet_id,)).fetchall())
        return wallet


def generate_wallet(mode: str = "single", trader_address: Optional[str] = None, label: Optional[str] = None) -> Dict[str, Any]:
    if mode != "pool" and count_wallets_by_mode("single") >= 5:
        raise ValueError("Single Copytrading slots are full: 5/5")
    if mode == "pool" and count_wallets_by_mode("pool") >= 3:
        raise ValueError("Multi Copytrading slots are full: 3/3")
    address = make_wallet_address()
    with get_db() as db:
        db.execute(
            """
            INSERT INTO copy_wallets
            (wallet_address, label, mode, status, copied_trader_address, value, available, total_pnl, realized_pnl, unrealized_pnl, gross_exposure, net_exposure, drift)
            VALUES (?, ?, ?, 'generated', ?, 0, 0, 0, 0, 0, 0, 0, 0)
            """,
            (address, label or "Generated Copy Wallet", mode, trader_address),
        )
        wallet_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        db.execute(
            """
            INSERT INTO copy_wallet_settings
            (wallet_id, copy_mode, multiplier, max_leverage, max_position_pct, max_gross_exposure_pct, stop_drawdown_pct, min_trade_size_usd, slippage_tolerance_pct)
            VALUES (?, 'proportional', 1.0, 3.0, 30.0, 150.0, -20.0, 10.0, 0.30)
            """,
            (wallet_id,),
        )
    return get_wallet(wallet_id)


def activate_wallet(wallet_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as db:
        wallet = db.execute("SELECT * FROM copy_wallets WHERE id = ?", (wallet_id,)).fetchone()
        if not wallet:
            return None
        if wallet["value"] <= 0:
            demo_value = random.choice([5000, 7500, 10000, 12500])
            db.execute(
                """
                UPDATE copy_wallets
                SET status='active', value=?, available=?, total_pnl=0, realized_pnl=0, unrealized_pnl=0,
                    gross_exposure=1.0, net_exposure=0.4, drift=1.0, activated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (demo_value, demo_value * 0.38, wallet_id),
            )
            seed_wallet_positions(db, wallet_id, demo_value)
        else:
            db.execute("UPDATE copy_wallets SET status='active', activated_at=CURRENT_TIMESTAMP WHERE id=?", (wallet_id,))
    return get_wallet(wallet_id)


def pause_wallet(wallet_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as db:
        existing = db.execute("SELECT id FROM copy_wallets WHERE id = ?", (wallet_id,)).fetchone()
        if not existing:
            return None
        db.execute("UPDATE copy_wallets SET status='paused' WHERE id=?", (wallet_id,))
    return get_wallet(wallet_id)


def close_wallet(wallet_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as db:
        existing = db.execute("SELECT id FROM copy_wallets WHERE id = ?", (wallet_id,)).fetchone()
        if not existing:
            return None
        db.execute("UPDATE copy_wallets SET status='closed' WHERE id=?", (wallet_id,))
    return get_wallet(wallet_id)


def delete_wallet(wallet_id: int) -> bool:
    with get_db() as db:
        wallet = db.execute("SELECT id, pool_id FROM copy_wallets WHERE id = ?", (wallet_id,)).fetchone()
        if not wallet:
            return False
        pool_id = wallet["pool_id"]
        db.execute("DELETE FROM copy_wallet_positions WHERE wallet_id = ?", (wallet_id,))
        db.execute("DELETE FROM copy_wallet_settings WHERE wallet_id = ?", (wallet_id,))
        db.execute("DELETE FROM copy_wallets WHERE id = ?", (wallet_id,))
        if pool_id:
            db.execute("DELETE FROM copy_pool_members WHERE pool_id = ?", (pool_id,))
            db.execute("DELETE FROM copy_pools WHERE id = ?", (pool_id,))
    return True


def patch_settings(wallet_id: int, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    allowed = [k for k, v in payload.items() if v is not None]
    if not allowed:
        return get_wallet(wallet_id)
    with get_db() as db:
        exists = db.execute("SELECT wallet_id FROM copy_wallet_settings WHERE wallet_id = ?", (wallet_id,)).fetchone()
        if not exists:
            db.execute(
                """
                INSERT INTO copy_wallet_settings
                (wallet_id, copy_mode, multiplier, max_leverage, max_position_pct, max_gross_exposure_pct,
                 stop_drawdown_pct, min_trade_size_usd, slippage_tolerance_pct)
                VALUES (?, 'proportional', 1.0, 3.0, 30.0, 150.0, -20.0, 10.0, 0.30)
                """,
                (wallet_id,),
            )
        assignments = ", ".join([f"{key} = ?" for key in allowed])
        values = [payload[key] for key in allowed] + [wallet_id]
        db.execute(f"UPDATE copy_wallet_settings SET {assignments} WHERE wallet_id = ?", values)
    return get_wallet(wallet_id)


def seed_wallet_positions(db: sqlite3.Connection, wallet_id: int, value: float):
    db.execute("DELETE FROM copy_wallet_positions WHERE wallet_id = ?", (wallet_id,))
    rows = [
        (wallet_id, "BTC", "Long", value * 0.22, value * 0.218, -0.9, 0.0, 0.0),
        (wallet_id, "ETH", "Long", value * 0.16, value * 0.162, 1.2, 0.0, 0.0),
        (wallet_id, "SOL", "Short", value * 0.08, value * 0.079, -1.1, 0.0, 0.0),
    ]
    db.executemany(
        """
        INSERT INTO copy_wallet_positions
        (wallet_id, coin, side, target_notional, actual_notional, drift_pct, pnl, pnl_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def live_positions() -> List[Dict[str, Any]]:
    with get_db() as db:
        return rows_to_dicts(
            db.execute(
                """
                SELECT w.id AS wallet_id, w.label AS wallet_label, p.coin, p.side, p.target_notional,
                       p.actual_notional, p.drift_pct, p.pnl, p.pnl_pct
                FROM copy_wallet_positions p
                JOIN copy_wallets w ON w.id = p.wallet_id
                ORDER BY ABS(p.actual_notional) DESC
                """
            ).fetchall()
        )


def list_pools() -> List[Dict[str, Any]]:
    with get_db() as db:
        pools = rows_to_dicts(db.execute("SELECT * FROM copy_pools ORDER BY id DESC").fetchall())
        for pool in pools:
            pool["members"] = rows_to_dicts(
                db.execute(
                    """
                    SELECT m.trader_address, m.weight, t.score, t.pnl_30d, t.risk
                    FROM copy_pool_members m
                    LEFT JOIN smart_traders t ON t.address = m.trader_address
                    WHERE m.pool_id = ?
                    """,
                    (pool["id"],),
                ).fetchall()
            )
        return pools


def create_pool(name: str, trader_addresses: List[str], multiplier: float) -> Dict[str, Any]:
    """
    Create a multi-copy pool and its backing copy wallet in one SQLite transaction.
    This avoids nested write connections and prevents `database is locked`.
    """
    clean_addresses = []
    for addr in trader_addresses:
        if addr and addr not in clean_addresses:
            clean_addresses.append(addr)

    if len(clean_addresses) < 2:
        raise ValueError("Multi copytrading requires at least 2 wallets")
    if len(clean_addresses) > 5:
        clean_addresses = clean_addresses[:5]

    weight = round(100 / len(clean_addresses), 2)
    address = make_wallet_address()

    with get_db() as db:
        db.execute("INSERT INTO copy_pools (name, status, multiplier) VALUES (?, 'paper', ?)", (name, multiplier))
        pool_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        for addr in clean_addresses:
            db.execute(
                "INSERT INTO copy_pool_members (pool_id, trader_address, weight) VALUES (?, ?, ?)",
                (pool_id, addr, weight),
            )

        db.execute(
            """
            INSERT INTO copy_wallets
            (wallet_address, label, mode, status, copied_trader_address, pool_id,
             value, available, total_pnl, realized_pnl, unrealized_pnl, gross_exposure, net_exposure, drift)
            VALUES (?, ?, 'pool', 'generated', NULL, ?, 0, 0, 0, 0, 0, 0, 0, 0)
            """,
            (address, name, pool_id),
        )
        wallet_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        db.execute(
            """
            INSERT INTO copy_wallet_settings
            (wallet_id, copy_mode, multiplier, max_leverage, max_position_pct, max_gross_exposure_pct,
             stop_drawdown_pct, min_trade_size_usd, slippage_tolerance_pct)
            VALUES (?, 'proportional', ?, 3.0, 30.0, 150.0, -20.0, 10.0, 0.30)
            """,
            (wallet_id, multiplier),
        )

        db.execute("UPDATE copy_pools SET wallet_id = ? WHERE id = ?", (wallet_id, pool_id))

    return [p for p in list_pools() if p["id"] == pool_id][0]

