import os
import random
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from .database import get_db, row_to_dict, rows_to_dicts
from .hydromancer_client import HydromancerClient, HydromancerError, normalize_leaderboard_row
from .hyperliquid_client import HyperliquidClient, HyperliquidError
from .token_icons import get_token_icon_url
from .market_registry import classify_coin, get_registry, registry_summary, refresh_registry, tradfi_asset_class, tradfi_dex_names, is_tradfi_dex_name

FATBOT_DEFAULT_VAULTS = [
    "0x0baFb25EF191bFe7A2727E14F5BbfC36610EC62A",
    "0x20c4F93BcAd80C7B83c20dEcA8A7bc91B9e6a3b0",
]

FATBOT_SELECTION_ADDRESSES = [
    "0x023a3d058020fb76cca98f01b3c48c8938a22355",
    "0xc926ddba8b7617dbc65712f20cf8e1b58b8598d3",
    "0x31DEA2516BEEE92135B96F464EEEC3CF292A13F2",
    "0x9DB82C502472D76742FDD69609DFCC6E01327401",
    "0x95FDE6CF0d305078B7EEaC44182A931c169DD947",
    "0x0C87080E84Ad8e91F54c4aF0AA921e1F183d601B",
    "0xb39766100347e1ffa1459492c85e8E3a2b25d3a0",
    "0xb3162a3C788399D9EC236c67A5af083dD78c8022",
    "0xA1b6D8EfbcB2fB750a84Dbc05649fA4968034F04",
    "0x6417da1D2452a4b4A81aa151b7235fFec865082f",
    "0x47807D3f6Ae34fF6aA1fc8Fe4e7B742197C1E125",
    "0x4DEc0A851849056E259128464EF28cE78aFa27F6",
    "0xa5Fd942D4bAdBab4FE84a9E10F565dd40d5f15Ff",
    "0x7a6d5fc57f6906f337c48fe2763c3a501304f79c",
    "0x13640f452a56aaa7a5a5e5a6bd24c45374dacbcc",
    "0x63d417a577b50c96f4f09148d4e4d70950db0522",
    "0x4ba1d152409f43ad92ba358886fe94bae4f5f656",
    "0xe8681168f59af16c60c805dab7842eb75f127879",
    "0x782e432267376f377585fc78092d998f8442ab83",
    "0x44c9c226cdfae773002b3f86d3966af3cd8f277c",
    "0x054a01da80ee37d5220af5471b1eedbdcd2cdb2f",
    "0x288ed4efc8fbd1e42a06fe083ea942d20c90b336",
    "0x309eE31b6986B4a04Abbfca79A80ADa94508e1dD",
    "0x4101CE19Ee81F24da894976E585f1E79119dBD93",
    "0x7f15F9E8f49c07Ab33D4DBd05a92DbD6dfd686ab",
    "0x223537ac9a856c31f4043e86ced86bb29f06653e",
    "0x727956612a8700627451204a3ae26268bd1a1525",
    "0x365e0c115f1ca1adcb42fd21142873493df7f880",
    "0xc6d7fdfbcb55d6cad6570c5838de394d2aa24015",
    "0x09f2b610f85a5fea4d35b42cccdc52f1f71d6bc7",
    "0x1643e9aba4fcfb4e8c1a887090239e34f488cad6",
    "0xf97ad6704baec104d00b88e0c157e2b7b3a1ddd1",
    "0x02fbbf39d1e3c142994b383af5ac3f2ad744cda9",
    "0xba939edf38c0ae0cc689c98b492e0535f43e4550",
    "0x7ab12f7a0925ef24927343d47199e75a91fc78aa",
    "0x7786498ffb58bedc6c392a4a40789be5c2da240d",
    "0x5559da6ec434c5723d0ce9c4da7f29e3f8a3d43b",
    "0x5f94a51948d2376ad34a6fadfa2544e651b74b96",
    "0x2d99fe0f36c1aebd28a1a2c0e82e8ca13c2ea351",
]

_FATBOT_VAULT_CACHE: Dict[str, Any] = {"ts": 0.0, "data": []}
_FATBOT_VAULT_CACHE_TTL_SECONDS = int(os.getenv("FATBOT_VAULT_CACHE_TTL_SECONDS", "60"))

_TRADER_LEADERBOARD_CACHE: Dict[str, Any] = {"ts": 0.0, "data": []}
_TRADER_LEADERBOARD_CACHE_TTL_SECONDS = int(os.getenv("TRADER_LEADERBOARD_CACHE_TTL_SECONDS", "60"))
_PROFILE_CACHE: Dict[str, Any] = {}
_PROFILE_CACHE_TTL_SECONDS = int(os.getenv("PROFILE_CACHE_TTL_SECONDS", "600"))

_LEADERBOARD_SNAPSHOT_LOCK = threading.Lock()
_LEADERBOARD_SNAPSHOT_WORKER_STARTED = False
_LEADERBOARD_SNAPSHOT_REFRESH_SECONDS = int(os.getenv("LEADERBOARD_SNAPSHOT_REFRESH_SECONDS", "300"))
_LEADERBOARD_SNAPSHOT_POOL_LIMIT = int(os.getenv("LEADERBOARD_SNAPSHOT_POOL_LIMIT", "200"))
_LEADERBOARD_SNAPSHOT_VISIBLE_LIMIT = int(os.getenv("LEADERBOARD_SNAPSHOT_VISIBLE_LIMIT", "50"))
_LEADERBOARD_SNAPSHOT_ENABLED = os.getenv("LEADERBOARD_SNAPSHOT_ENABLED", "true").lower() not in ("0", "false", "no", "off")
_LEADERBOARD_SNAPSHOT_CATEGORIES = ["trades", "tradfi", "crypto", "bull", "bear", "fatbot_selection"]
_LEADERBOARD_SNAPSHOT_VERSION = "v130-fatbot-public-hl"






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




def _leaderboard_snapshot_now() -> float:
    return time.time()


def _leaderboard_snapshot_rows_from_db(category: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    category = str(category or "trades").lower()
    with get_db() as db:
        meta = row_to_dict(db.execute(
            "SELECT category, updated_at, status, error FROM leaderboard_snapshots WHERE category = ?",
            (category,),
        ).fetchone())
        rows = db.execute(
            "SELECT payload FROM leaderboard_snapshot_rows WHERE category = ? ORDER BY rank ASC",
            (category,),
        ).fetchall()

    parsed: List[Dict[str, Any]] = []
    for row in rows:
        try:
            parsed.append(json.loads(row["payload"]))
        except Exception:
            continue
    return meta, parsed


def _leaderboard_snapshot_write(category: str, rows: List[Dict[str, Any]], status: str = "ready", error: Optional[str] = None) -> None:
    category = str(category or "trades").lower()
    now = _leaderboard_snapshot_now()
    clean_rows = []
    for idx, row in enumerate(rows or [], start=1):
        item = dict(row or {})
        item["rank"] = idx
        item["snapshot_category"] = category
        item["snapshot_updated_at"] = now
        item["snapshot_version"] = _LEADERBOARD_SNAPSHOT_VERSION
        clean_rows.append(item)

    with get_db() as db:
        db.execute(
            """
            INSERT INTO leaderboard_snapshots(category, updated_at, status, error)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(category) DO UPDATE SET
                updated_at = excluded.updated_at,
                status = excluded.status,
                error = excluded.error
            """,
            (category, now, status, error),
        )
        db.execute("DELETE FROM leaderboard_snapshot_rows WHERE category = ?", (category,))
        for idx, row in enumerate(clean_rows, start=1):
            db.execute(
                "INSERT INTO leaderboard_snapshot_rows(category, rank, payload) VALUES (?, ?, ?)",
                (category, idx, json.dumps(row, separators=(",", ":"), ensure_ascii=False)),
            )


def _leaderboard_snapshot_mark_error(category: str, error: str) -> None:
    # Preserve last good rows; only update status/error metadata.
    with get_db() as db:
        db.execute(
            """
            INSERT INTO leaderboard_snapshots(category, updated_at, status, error)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(category) DO UPDATE SET
                updated_at = excluded.updated_at,
                status = excluded.status,
                error = excluded.error
            """,
            (str(category or "trades").lower(), _leaderboard_snapshot_now(), "error", str(error or "unknown error")),
        )


def _leaderboard_sort_pnl(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def value(row: Dict[str, Any]) -> float:
        try:
            return float(row.get("total_pnl") or row.get("pnl_usd") or row.get("pnl") or 0)
        except Exception:
            return 0.0
    return sorted(rows or [], key=value, reverse=True)




def _leaderboard_snapshot_enrich_category_charts(rows: List[Dict[str, Any]], window: str = "30d") -> List[Dict[str, Any]]:
    """
    Ensure every final visible snapshot category row gets a mini chart when
    Hyperliquid portfolio history is available.

    v130:
    - First uses the existing bulk sparkline path.
    - Then retries missing rows through profile portfolio chart data.
    - This protects TradFi/Crypto/Bull/Bears and FatBot Selection from losing
      mini charts after category filtering.
    """
    if not rows:
        return rows

    old_limit = os.environ.get("TOP_TRADERS_SPARKLINE_ENRICH_LIMIT")
    try:
        os.environ["TOP_TRADERS_SPARKLINE_ENRICH_LIMIT"] = str(max(len(rows), _LEADERBOARD_SNAPSHOT_VISIBLE_LIMIT))
        enriched = _enrich_top_traders_pnl_sparkline([dict(r) for r in rows], {"window": window})
    finally:
        if old_limit is None:
            os.environ.pop("TOP_TRADERS_SPARKLINE_ENRICH_LIMIT", None)
        else:
            os.environ["TOP_TRADERS_SPARKLINE_ENRICH_LIMIT"] = old_limit

    missing_indexes = [idx for idx, row in enumerate(enriched) if not row.get("pnl_sparkline")]
    if not missing_indexes:
        return enriched

    try:
        workers = int(os.getenv("SNAPSHOT_PROFILE_CHART_FALLBACK_WORKERS", "8"))
    except Exception:
        workers = 8
    workers = max(1, min(workers, len(missing_indexes)))

    def attach_one(idx: int, row: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        address = str(row.get("address") or "")
        if not address:
            return idx, row
        try:
            updated = _attach_portfolio_chart_data(dict(row), address, {"window": window})
            return idx, updated
        except Exception as exc:
            row["snapshot_chart_fallback_status"] = f"error: {exc}"
            return idx, row

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(attach_one, idx, dict(enriched[idx])): idx for idx in missing_indexes}
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                out_idx, row = future.result()
                enriched[out_idx] = row
            except Exception:
                pass

    return enriched




def _fatbot_selection_apply_public_hl_portfolio_stats(row: Dict[str, Any], hl_client: HyperliquidClient, address: str) -> Dict[str, Any]:
    """
    Public Hyperliquid portfolio fallback for manual FatBot Selection.

    This fills PnL/volume/account value without relying on Hydromancer.
    """
    try:
        portfolio_stats = hl_client.portfolio_stats(address, "30d")
    except Exception as exc:
        row["portfolio_status"] = f"error: {exc}"
        return row

    if not portfolio_stats:
        return row

    row["portfolio_stats_source"] = portfolio_stats.get("source")
    row["portfolio_period"] = portfolio_stats.get("portfolio_period")

    try:
        pnl = portfolio_stats.get("pnl")
        if pnl is not None:
            row["total_pnl"] = float(pnl or 0)
            row["pnl_usd"] = row["total_pnl"]
            row["pnl_source"] = "hyperliquid_portfolio"
    except Exception:
        pass

    try:
        volume = portfolio_stats.get("volume")
        if volume is not None:
            row["volume"] = float(volume or 0)
            row["volume_traded"] = row["volume"]
    except Exception:
        pass

    try:
        account_value = portfolio_stats.get("account_value")
        if account_value is not None and float(account_value or 0) > 0:
            row["account_value"] = float(account_value or 0)
            row["account_value_source"] = "hyperliquid_portfolio"
    except Exception:
        pass

    return row


def _fatbot_selection_apply_public_hl_fill_stats(row: Dict[str, Any], hl_client: HyperliquidClient, address: str) -> Dict[str, Any]:
    """
    Public Hyperliquid fills fallback for volume/trades/win-rate.
    """
    try:
        fill_stats = hl_client.user_30d_fill_stats(address, "30d")
    except Exception as exc:
        row["fills_status"] = f"error: {exc}"
        return row

    if not fill_stats:
        return row

    try:
        if not row.get("volume"):
            row["volume"] = float(fill_stats.get("volume") or 0)
            row["volume_traded"] = row["volume"]
    except Exception:
        pass

    try:
        row["trades"] = int(fill_stats.get("fills") or row.get("trades") or 0)
        row["total_trades"] = row["trades"]
    except Exception:
        pass

    try:
        row["win_rate"] = float(fill_stats.get("win_rate") or row.get("win_rate") or 0)
    except Exception:
        pass

    # Use closed PnL only when portfolio did not provide PnL.
    try:
        if not row.get("pnl_source"):
            row["total_pnl"] = float(fill_stats.get("closed_pnl") or row.get("total_pnl") or 0)
            row["pnl_usd"] = row["total_pnl"]
            row["pnl_source"] = "hyperliquid_userFillsByTime"
    except Exception:
        pass

    return row



def _leaderboard_snapshot_build_fatbot_selection() -> List[Dict[str, Any]]:
    """
    Manual FatBot Selection built from public Hyperliquid endpoints only.

    v130:
    - every manual wallet is scanned directly;
    - positions are fetched across all relevant dexes;
    - wallets with no open positions are hidden;
    - PnL/volume/account value come from public HL portfolio/fills;
    - mini/profile charts are attached from public HL portfolio history.
    """
    addresses: List[str] = []
    seen = set()
    for address in FATBOT_SELECTION_ADDRESSES:
        addr = str(address or "").strip()
        if not addr:
            continue
        key = addr.lower()
        if key in seen:
            continue
        seen.add(key)
        addresses.append(addr)

    if not addresses:
        return []

    base_rows: List[Dict[str, Any]] = []
    for idx, address in enumerate(addresses, start=1):
        base_rows.append({
            "address": address,
            "label": f"FatBot Selection #{idx}",
            "source": "fatbot_selection",
            "rank": idx,
            "is_fatbot_selection": True,
            "total_pnl": 0,
            "pnl_usd": 0,
            "pnl_source": "not_loaded",
            "volume": 0,
            "volume_traded": 0,
            "win_rate": 0,
            "trades": 0,
            "total_trades": 0,
            "days_active": 0,
            "account_age_days": 0,
            "account_value": 0,
            "positions": [],
            "open_positions": 0,
            "leaderboard_window": "30d",
            "leaderboard_sort_by": "totalPnl",
            "requested_market_type": "fatbot_selection",
        })

    try:
        workers = int(os.getenv("FATBOT_SELECTION_WORKERS", "10"))
    except Exception:
        workers = 10
    workers = max(1, min(workers, len(base_rows)))

    def enrich_one(item: Dict[str, Any]) -> Dict[str, Any]:
        address = str(item.get("address") or "")
        if not address:
            return item

        try:
            hl_client = HyperliquidClient()
            try:
                all_mids = hl_client.all_mids()
            except Exception:
                all_mids = {}

            # Public current positions across main + relevant HIP-3/XYZ dexes.
            hl_state, positions, dex_status = _hyperliquid_positions_all_relevant_dexes(hl_client, address, all_mids=all_mids)
            item["dex_state_status"] = dex_status
            item["hl_state_status"] = "ok" if (hl_state or positions) else "empty"

            if hl_state:
                item["account_value"] = _extract_account_value_from_state(hl_state) or item.get("account_value", 0)
                item["margin_summary"] = hl_state.get("marginSummary") or hl_state.get("crossMarginSummary") or {}

            item["positions"] = positions or []
            item["open_positions"] = len(item["positions"])
            item = _attach_current_exposure_metrics(item)
            if item.get("positions"):
                item = _attach_market_type_metrics(item)

            # Public HL stats. Portfolio is primary for PnL/account value/volume;
            # fills are fallback for trades/win rate/volume.
            item = _fatbot_selection_apply_public_hl_portfolio_stats(item, hl_client, address)
            item = _fatbot_selection_apply_public_hl_fill_stats(item, hl_client, address)

            if not item.get("account_value"):
                item["account_value"] = _account_value_from_portfolio_fallback(hl_client, address, "30d")
                if item.get("account_value"):
                    item["account_value_source"] = "hyperliquid_portfolio_fallback"

            item = _attach_portfolio_chart_data(item, address, {"window": "30d"})

            account_value = float(item.get("account_value") or 0)
            total_pnl = float(item.get("total_pnl") or item.get("pnl_usd") or 0)
            item["total_pnl"] = total_pnl
            item["pnl_usd"] = total_pnl
            item["pnl_pct"] = (total_pnl / account_value * 100.0) if account_value else 0.0
            item["pnl_display_mode"] = "usd"

        except Exception as exc:
            item["hl_state_status"] = f"fatbot_selection_error: {exc}"
            item.setdefault("positions", [])
            item.setdefault("open_positions", 0)

        return item

    enriched: List[Optional[Dict[str, Any]]] = [None] * len(base_rows)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(enrich_one, dict(row)): idx for idx, row in enumerate(base_rows)}
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                enriched[idx] = future.result()
            except Exception:
                enriched[idx] = base_rows[idx]

    visible: List[Dict[str, Any]] = []
    hidden_no_positions = 0
    for idx, enriched_item in enumerate(enriched):
        row = enriched_item if enriched_item is not None else base_rows[idx]
        if int(row.get("open_positions") or 0) > 0 or bool(row.get("positions")):
            visible.append(row)
        else:
            hidden_no_positions += 1

    visible = _leaderboard_sort_pnl(visible)
    visible = _leaderboard_snapshot_enrich_category_charts(visible, "30d")

    for idx, row in enumerate(visible, start=1):
        row["rank"] = idx
        row["snapshot_category"] = "fatbot_selection"
        row["fatbot_selection_hidden_no_positions_count"] = hidden_no_positions
        row["fatbot_selection_total_manual_wallets"] = len(base_rows)
        row["snapshot_version"] = _LEADERBOARD_SNAPSHOT_VERSION

    return visible


def _leaderboard_snapshot_build_from_pool(pool: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    visible = max(1, int(_LEADERBOARD_SNAPSHOT_VISIBLE_LIMIT or 50))
    rows = [dict(r) for r in (pool or []) if r.get("address")]

    trades = _leaderboard_sort_pnl(rows)[:visible]
    tradfi = _leaderboard_sort_pnl([
        r for r in rows
        if float(r.get("tradfi_position_count_pct") or 0) >= float(_market_type_config().get("tradfi_position_count_threshold") or 70)
    ])[:visible]
    crypto = _leaderboard_sort_pnl([
        r for r in rows
        if float(r.get("crypto_exposure_pct") or 0) >= float(_market_type_config().get("crypto_threshold") or 70)
    ])[:visible]
    bull = _leaderboard_sort_pnl([
        r for r in rows
        if float(r.get("long_exposure_share_pct") or r.get("long_exposure_pct") or 0) > 80
    ])[:visible]
    bear = _leaderboard_sort_pnl([
        r for r in rows
        if float(r.get("short_exposure_share_pct") or r.get("short_exposure_pct") or 0) > 80
    ])[:visible]

    return {
        "trades": trades,
        "tradfi": tradfi,
        "crypto": crypto,
        "bull": bull,
        "bear": bear,
    }


def precompute_leaderboard_snapshots(force: bool = False) -> Dict[str, Any]:
    if not _LEADERBOARD_SNAPSHOT_ENABLED:
        return {"ok": False, "enabled": False, "reason": "disabled"}

    if not _LEADERBOARD_SNAPSHOT_LOCK.acquire(blocking=False):
        return {"ok": False, "running": True}

    started = _leaderboard_snapshot_now()
    try:
        # One enriched all-market pool, then split into fixed categories.
        # This avoids running separate slow Hyperliquid/XYZ scans per user click.
        pool_limit = max(_LEADERBOARD_SNAPSHOT_VISIBLE_LIMIT, _LEADERBOARD_SNAPSHOT_POOL_LIMIT)
        pool = list_traders(
            force_refresh=force,
            window="30d",
            sort_by="totalPnl",
            limit=pool_limit,
            min_trades=0,
            min_days_active=0,
            market_type="all",
        )

        category_rows = _leaderboard_snapshot_build_from_pool(pool)
        category_rows["fatbot_selection"] = _leaderboard_snapshot_build_fatbot_selection()

        # Critical: after filtering into categories, enrich the final visible rows
        # again so mini charts are present in every category, not only in Top Trades.
        for category, rows in list(category_rows.items()):
            category_rows[category] = _leaderboard_snapshot_enrich_category_charts(rows, "30d")

        for category, rows in category_rows.items():
            _leaderboard_snapshot_write(category, rows, status="ready", error=None)

        return {
            "ok": True,
            "enabled": True,
            "duration_seconds": round(_leaderboard_snapshot_now() - started, 3),
            "categories": {k: len(v) for k, v in category_rows.items()},
        }
    except Exception as exc:
        err = str(exc)
        for category in _LEADERBOARD_SNAPSHOT_CATEGORIES:
            _leaderboard_snapshot_mark_error(category, err)
        return {"ok": False, "enabled": True, "error": err}
    finally:
        _LEADERBOARD_SNAPSHOT_LOCK.release()


def get_leaderboard_snapshot(category: str = "trades") -> Dict[str, Any]:
    category = str(category or "trades").lower()
    if category == "top":
        category = "trades"
    if category not in set(_LEADERBOARD_SNAPSHOT_CATEGORIES):
        category = "trades"

    meta, rows = _leaderboard_snapshot_rows_from_db(category)
    running = _LEADERBOARD_SNAPSHOT_LOCK.locked()

    stale_version = bool(rows) and any(str(row.get("snapshot_version") or "") != _LEADERBOARD_SNAPSHOT_VERSION for row in rows[:3])

    if (not meta) or stale_version:
        # Kick off a background build, but do not block the user request.
        start_leaderboard_snapshot_worker(run_once=True)
        return {
            "category": category,
            "status": "preparing" if not stale_version else "refreshing",
            "updated_at": meta.get("updated_at") if meta else None,
            "age_seconds": None,
            "running": True,
            "rows": [] if stale_version else [],
            "error": None,
        }

    age = max(0.0, _leaderboard_snapshot_now() - float(meta.get("updated_at") or 0))
    return {
        "category": category,
        "status": meta.get("status") or ("ready" if rows else "preparing"),
        "updated_at": meta.get("updated_at"),
        "age_seconds": round(age, 1),
        "running": running,
        "rows": rows,
        "error": meta.get("error"),
    }


def get_leaderboard_snapshot_status() -> Dict[str, Any]:
    out = {"enabled": _LEADERBOARD_SNAPSHOT_ENABLED, "running": _LEADERBOARD_SNAPSHOT_LOCK.locked(), "categories": {}}
    for category in _LEADERBOARD_SNAPSHOT_CATEGORIES:
        meta, rows = _leaderboard_snapshot_rows_from_db(category)
        if not meta:
            out["categories"][category] = {"status": "missing", "rows": 0, "age_seconds": None, "updated_at": None}
        else:
            age = max(0.0, _leaderboard_snapshot_now() - float(meta.get("updated_at") or 0))
            out["categories"][category] = {
                "status": meta.get("status"),
                "rows": len(rows),
                "age_seconds": round(age, 1),
                "updated_at": meta.get("updated_at"),
                "error": meta.get("error"),
            }
    return out


def start_leaderboard_snapshot_worker(run_once: bool = False) -> Dict[str, Any]:
    global _LEADERBOARD_SNAPSHOT_WORKER_STARTED
    if not _LEADERBOARD_SNAPSHOT_ENABLED:
        return {"started": False, "enabled": False}

    def worker_loop() -> None:
        while True:
            try:
                precompute_leaderboard_snapshots(force=False)
            except Exception as exc:
                print(f"[leaderboard-snapshot] refresh failed: {exc}")
            if run_once:
                break
            time.sleep(max(30, int(_LEADERBOARD_SNAPSHOT_REFRESH_SECONDS or 300)))

    if run_once:
        thread = threading.Thread(target=worker_loop, daemon=True, name="leaderboard-snapshot-once")
        thread.start()
        return {"started": True, "once": True}

    if _LEADERBOARD_SNAPSHOT_WORKER_STARTED:
        return {"started": False, "already_started": True, "enabled": True}

    _LEADERBOARD_SNAPSHOT_WORKER_STARTED = True
    thread = threading.Thread(target=worker_loop, daemon=True, name="leaderboard-snapshot-worker")
    thread.start()
    return {"started": True, "enabled": True, "refresh_seconds": _LEADERBOARD_SNAPSHOT_REFRESH_SECONDS}



def _normalize_leaderboard_filters(
    window: str = "30d",
    sort_by: str = "totalPnl",
    limit: int = 50,
    min_trades: int = 0,
    min_days_active: int = 0,
    market_type: str = "all",
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
    limit = max(1, min(500, limit))

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

    market_type = str(market_type or "all").lower()
    if market_type not in {"all", "crypto", "tradfi", "tradfi_any"}:
        market_type = "all"

    return {
        "window": window,
        "sort_by": sort_by,
        "limit": limit,
        "min_trades": min_trades,
        "min_days_active": min_days_active,
        "market_type": market_type,
    }


def _leaderboard_cache_key(prefix: str, filters: Dict[str, Any]) -> str:
    return "|".join([
        prefix,
        str(filters.get("window")),
        str(filters.get("sort_by")),
        str(filters.get("limit")),
        str(filters.get("min_trades")),
        str(filters.get("min_days_active")),
        str(filters.get("market_type", "all")),
    ])



def _market_type_config() -> Dict[str, Any]:
    # Separate thresholds:
    # - Crypto remains stricter by default.
    # - TradFi/XYZ now uses the same 70% dominance idea as Crypto,
    #   but based on open-position count share.
    crypto_threshold = float(os.getenv("MARKET_TYPE_CRYPTO_THRESHOLD", os.getenv("MARKET_TYPE_EXPOSURE_THRESHOLD", "70")))
    tradfi_threshold = float(os.getenv("MARKET_TYPE_TRADFI_THRESHOLD", "70"))
    tradfi_position_count_threshold = float(os.getenv("MARKET_TYPE_TRADFI_POSITION_COUNT_THRESHOLD", "70"))

    registry = get_registry(force_refresh=False)
    return {
        "registry": registry,
        "crypto_threshold": crypto_threshold,
        "tradfi_threshold": tradfi_threshold,
        "tradfi_position_count_threshold": tradfi_position_count_threshold,
        # Backwards-compatible generic threshold used only for debug display.
        "threshold": tradfi_threshold,
    }



def _normalize_coin_symbol(coin: str) -> str:
    raw = str(coin or "").upper().strip()
    if ":" in raw:
        raw = raw.split(":")[-1]
    return raw


def _attach_market_type_metrics(row: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _market_type_config()

    positions = row.get("positions") or []
    tradfi_notional = 0.0
    crypto_notional = 0.0
    tradfi_position_count = 0
    crypto_position_count = 0
    coin_breakdown: List[Dict[str, Any]] = []

    for pos in positions:
        try:
            notional = abs(float(pos.get("notional") or 0))
        except Exception:
            notional = 0.0

        coin_raw = str(pos.get("coin") or "")
        coin = _normalize_coin_symbol(coin_raw)
        pos_dex = str(pos.get("dex") or "").strip().lower()
        market = classify_coin(coin_raw, dex=pos_dex)
        asset_class = tradfi_asset_class(coin_raw, dex=pos_dex)

        if market == "tradfi":
            tradfi_notional += notional
            tradfi_position_count += 1
        else:
            crypto_notional += notional
            crypto_position_count += 1

        coin_breakdown.append({
            "coin": coin_raw,
            "normalized_coin": coin,
            "dex": pos_dex,
            "qualified_coin": f"{pos_dex}:{coin_raw}" if pos_dex else coin_raw,
            "market_type": market,
            "asset_class": asset_class,
            "notional": notional,
        })

    gross = tradfi_notional + crypto_notional
    total_position_count = tradfi_position_count + crypto_position_count
    tradfi_pct = (tradfi_notional / gross * 100) if gross else 0.0
    crypto_pct = (crypto_notional / gross * 100) if gross else 0.0
    tradfi_position_count_pct = (tradfi_position_count / total_position_count * 100) if total_position_count else 0.0
    crypto_position_count_pct = (crypto_position_count / total_position_count * 100) if total_position_count else 0.0

    row["tradfi_notional"] = tradfi_notional
    row["crypto_notional"] = crypto_notional
    row["tradfi_exposure_pct"] = tradfi_pct
    row["crypto_exposure_pct"] = crypto_pct
    row["tradfi_position_count"] = tradfi_position_count
    row["crypto_position_count"] = crypto_position_count
    row["total_position_count"] = total_position_count
    row["tradfi_position_count_pct"] = tradfi_position_count_pct
    row["crypto_position_count_pct"] = crypto_position_count_pct
    row["has_tradfi_position"] = tradfi_position_count > 0
    row["has_crypto_position"] = crypto_position_count > 0
    row["market_coin_breakdown"] = coin_breakdown

    tradfi_threshold = cfg.get("tradfi_threshold", 40)
    tradfi_position_count_threshold = cfg.get("tradfi_position_count_threshold", 40)
    crypto_threshold = cfg.get("crypto_threshold", 70)
    if total_position_count <= 0:
        row["market_type"] = "none"
        row["market_type_reason"] = "no_open_positions"
    elif tradfi_position_count_pct >= tradfi_position_count_threshold:
        row["market_type"] = "tradfi"
        row["market_type_reason"] = "tradfi_position_count_threshold_met"
    elif crypto_pct >= crypto_threshold:
        row["market_type"] = "crypto"
        row["market_type_reason"] = "crypto_exposure_threshold_met"
    else:
        row["market_type"] = "mixed"
        row["market_type_reason"] = "tradfi_position_count_below_threshold" if tradfi_position_count > 0 else "below_threshold"

    return row



def _apply_local_leaderboard_filters(rows: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    min_trades = int(filters.get("min_trades") or 0)
    min_days = int(filters.get("min_days_active") or 0)
    limit = int(filters.get("limit") or 50)
    sort_by = str(filters.get("sort_by") or "totalPnl")
    market_type = str(filters.get("market_type") or "all")

    filtered = []
    for row in rows:
        trades = int(row.get("total_trades") or row.get("trades") or 0)
        days = int(row.get("days_active") or row.get("account_age_days") or 0)
        if trades < min_trades:
            continue
        if days < min_days:
            continue
        if market_type != "all":
            row_market = str(row.get("market_type") or "").lower()
            # TradFi filter is based on count of open positions, not exposure notional.
            # Example: 10 open positions, 7 TradFi = 70%.
            if market_type == "tradfi_any":
                # Discovery mode: show any wallet with at least one current TradFi/XYZ/SPX position.
                if not (bool(row.get("has_tradfi_position")) or int(row.get("tradfi_position_count") or 0) > 0):
                    continue
            elif market_type == "tradfi":
                # Strict mode: TradFi open-position count share must be >= threshold.
                cfg = _market_type_config()
                threshold = float(cfg.get("tradfi_position_count_threshold") or 40)
                count_pct = float(row.get("tradfi_position_count_pct") or 0)
                if count_pct < threshold:
                    continue
            else:
                # Crypto keeps the threshold-based exposure rule.
                if row_market != market_type:
                    continue
        filtered.append(row)

    def sort_value(row: Dict[str, Any]) -> float:
        if sort_by == "volume":
            return float(row.get("volume") or row.get("volume_traded") or 0)
        if sort_by == "winRate":
            return float(row.get("win_rate") or 0)
        return float(row.get("total_pnl") or row.get("pnl_usd") or row.get("pnl_pct") or 0)

    filtered.sort(key=sort_value, reverse=True)
    out = filtered[:limit]
    for row in out:
        if market_type != "all":
            row["active_market_filter"] = market_type
            cfg = _market_type_config()
            row["market_filter_threshold"] = (
                0 if market_type == "tradfi_any"
                else cfg.get("tradfi_position_count_threshold") if market_type == "tradfi"
                else cfg.get("crypto_threshold")
            )
            row["market_filter_mode"] = (
                "any_tradfi_position" if market_type == "tradfi_any"
                else "position_count_pct" if market_type == "tradfi"
                else "exposure_threshold"
            )
    return out

def get_market_registry() -> Dict[str, Any]:
    return registry_summary()


def refresh_market_registry() -> Dict[str, Any]:
    refresh_registry()
    return registry_summary()


def debug_tradfi_scan(
    window: str = "30d",
    sort_by: str = "totalPnl",
    limit: int = 500,
    min_trades: int = 0,
    min_days_active: int = 0,
) -> Dict[str, Any]:
    filters = _normalize_leaderboard_filters(window, sort_by, limit, min_trades, min_days_active, "tradfi")
    client = HydromancerClient()
    if not client.enabled:
        return {"status": "hydromancer_disabled"}

    candidates = _hydromancer_market_type_candidates(client, filters)
    enriched = _enrich_top_traders_with_current_exposure(candidates)

    with_positions = [r for r in enriched if int(r.get("open_positions") or 0) > 0]
    tradfi_threshold = float(_market_type_config().get("tradfi_position_count_threshold") or 40)
    tradfi_any_rows = [r for r in enriched if bool(r.get("has_tradfi_position")) or int(r.get("tradfi_position_count") or 0) > 0]
    tradfi_rows = [r for r in enriched if float(r.get("tradfi_position_count_pct") or 0) >= tradfi_threshold]
    mixed_rows = [r for r in enriched if str(r.get("market_type") or "").lower() == "mixed"]

    coin_counts: Dict[str, Dict[str, Any]] = {}
    for row in enriched:
        for p in row.get("positions") or []:
            coin = str(p.get("coin") or "?")
            dex = str(p.get("dex") or "").strip().lower()
            market = classify_coin(coin, dex=dex)
            asset_class = tradfi_asset_class(coin, dex=dex)
            qualified_coin = f"{dex}:{coin}" if dex else coin
            key = f"{market}:{asset_class}:{qualified_coin}"
            if key not in coin_counts:
                coin_counts[key] = {"coin": coin, "dex": dex, "qualified_coin": qualified_coin, "market_type": market, "asset_class": asset_class, "count": 0, "notional": 0.0}
            coin_counts[key]["count"] += 1
            try:
                coin_counts[key]["notional"] += abs(float(p.get("notional") or 0))
            except Exception:
                pass

    return {
        "status": "ok",
        "filters": filters,
        "candidate_count": len(candidates),
        "enriched_count": len(enriched),
        "with_open_positions_count": len(with_positions),
        "tradfi_count": len(tradfi_rows),
        "tradfi_any_count": len(tradfi_any_rows),
        "tradfi_presence_count": len(tradfi_any_rows),
        "mixed_count": len(mixed_rows),
        "thresholds": {
            "tradfi_position_count": _market_type_config().get("tradfi_position_count_threshold"),
            "tradfi_exposure": _market_type_config().get("tradfi_threshold"),
            "crypto": _market_type_config().get("crypto_threshold"),
        },
        "coin_counts": sorted(coin_counts.values(), key=lambda x: x.get("notional", 0), reverse=True)[:100],
        "tradfi_rows": [
            {
                "address": r.get("address"),
                "rank": r.get("rank"),
                "source_sort": r.get("market_scan_source_sort"),
                "tradfi_exposure_pct": r.get("tradfi_exposure_pct"),
                "crypto_exposure_pct": r.get("crypto_exposure_pct"),
                "tradfi_position_count": r.get("tradfi_position_count"),
                "total_position_count": r.get("total_position_count"),
                "tradfi_position_count_pct": r.get("tradfi_position_count_pct"),
                "open_positions": r.get("open_positions"),
                "coins": [p.get("coin") for p in (r.get("positions") or [])],
            }
            for r in tradfi_rows[:50]
        ],
        "tradfi_any_rows": [
            {
                "address": r.get("address"),
                "rank": r.get("rank"),
                "source_sort": r.get("market_scan_source_sort"),
                "tradfi_exposure_pct": r.get("tradfi_exposure_pct"),
                "crypto_exposure_pct": r.get("crypto_exposure_pct"),
                "tradfi_position_count": r.get("tradfi_position_count"),
                "total_position_count": r.get("total_position_count"),
                "tradfi_position_count_pct": r.get("tradfi_position_count_pct"),
                "open_positions": r.get("open_positions"),
                "coins": [p.get("coin") for p in (r.get("positions") or [])],
            }
            for r in tradfi_any_rows[:50]
        ],
        "sample": [
            {
                "rank": r.get("rank"),
                "address": r.get("address"),
                "source_sort": r.get("market_scan_source_sort"),
                "open_positions": r.get("open_positions"),
                "market_type": r.get("market_type"),
                "market_type_reason": r.get("market_type_reason"),
                "tradfi_exposure_pct": r.get("tradfi_exposure_pct"),
                "crypto_exposure_pct": r.get("crypto_exposure_pct"),
                "coins": [p.get("coin") for p in (r.get("positions") or [])],
                "hl_state_status": r.get("hl_state_status"),
            }
            for r in enriched[:100]
        ],
    }


def debug_profile_lookup(address: str) -> Dict[str, Any]:
    cached = _find_trader_in_leaderboard_caches(address)
    out: Dict[str, Any] = {
        "address": address,
        "found_in_leaderboard_cache_with_positions": cached is not None,
        "cache_summary": [],
    }

    for cache_name, cache in [
        ("trader_leaderboard", _TRADER_LEADERBOARD_CACHE),
        ("fatbot_vault", _FATBOT_VAULT_CACHE),
    ]:
        for cache_key, item in list(cache.items()):
            try:
                data = item.get("data") if isinstance(item, dict) else item
                if not isinstance(data, list):
                    continue
                target = str(address or "").lower()
                matching_rows = [
                    row for row in data
                    if isinstance(row, dict) and str(row.get("address") or "").lower() == target
                ]
                out["cache_summary"].append({
                    "cache": cache_name,
                    "key": str(cache_key),
                    "rows": len(data),
                    "contains_address": bool(matching_rows),
                    "matching_rows": len(matching_rows),
                    "matching_rows_with_positions": sum(1 for row in matching_rows if row.get("positions")),
                })
            except Exception as exc:
                out["cache_summary"].append({
                    "cache": cache_name,
                    "key": str(cache_key),
                    "error": str(exc),
                })

    metadata = _find_trader_row_in_leaderboard_caches(address)
    if metadata:
        out["cached_metadata_row"] = {
            "address": metadata.get("address"),
            "rank": metadata.get("rank"),
            "account_value": metadata.get("account_value"),
            "account_value_source": metadata.get("account_value_source"),
            "total_pnl": metadata.get("total_pnl"),
            "volume": metadata.get("volume") or metadata.get("volume_traded"),
            "win_rate": metadata.get("win_rate"),
            "open_positions": metadata.get("open_positions"),
            "positions_count": len(metadata.get("positions") or []),
            "leaderboard_cache_source": metadata.get("leaderboard_cache_source"),
        }

    if cached:
        out["cached_row"] = {
            "address": cached.get("address"),
            "rank": cached.get("rank"),
            "source": cached.get("source"),
            "market_type": cached.get("market_type"),
            "market_type_reason": cached.get("market_type_reason"),
            "open_positions": cached.get("open_positions"),
            "positions_count": len(cached.get("positions") or []),
            "coins": [
                {
                    "coin": p.get("coin"),
                    "dex": p.get("dex"),
                    "side": p.get("side"),
                    "notional": p.get("notional"),
                }
                for p in (cached.get("positions") or [])
            ],
            "profile_mode": cached.get("profile_mode"),
            "profile_cache_source": cached.get("profile_cache_source"),
        }

    return out


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



def _portfolio_bucket_from_payload(payload: Any, window: str = "7d") -> Optional[Dict[str, Any]]:
    target = str(window or "7d").lower()
    period_map = {
        "1d": ("day", "1d"),
        "7d": ("week", "7d"),
        "30d": ("month", "30d"),
        "all": ("allTime", "all", "all_time"),
    }
    aliases = period_map.get(target, ("week", "7d"))

    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                if str(item[0]) in aliases and isinstance(item[1], dict):
                    return item[1]
            elif isinstance(item, dict):
                period = str(item.get("period") or item.get("timeframe") or item.get("window") or "")
                if period in aliases:
                    return item

    if isinstance(payload, dict):
        for key in aliases:
            value = payload.get(key)
            if isinstance(value, dict):
                return value

        nested = payload.get("data") or payload.get("result")
        if isinstance(nested, dict):
            for key in aliases:
                value = nested.get(key)
                if isinstance(value, dict):
                    return value

    return None


def _float_from_history_point(point: Any) -> Optional[float]:
    try:
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            return float(str(point[1]).replace("$", "").replace(",", "").strip())
        if isinstance(point, dict):
            value = (
                point.get("pnl")
                or point.get("value")
                or point.get("y")
                or point.get("totalPnl")
                or point.get("cumPnl")
                or point.get("cumulativePnl")
            )
            if value is None:
                return None
            return float(str(value).replace("$", "").replace(",", "").strip())
    except Exception:
        return None
    return None


def _downsample(values: List[float], max_points: int = 20) -> List[float]:
    if len(values) <= max_points:
        return values
    if max_points <= 2:
        return [values[0], values[-1]]
    out: List[float] = []
    last_index = len(values) - 1
    for i in range(max_points):
        idx = round(i * last_index / (max_points - 1))
        out.append(values[idx])
    return out


def _pnl_sparkline_from_portfolio_payload(payload: Any, window: str = "7d") -> List[float]:
    bucket = _portfolio_bucket_from_payload(payload, window)
    if not isinstance(bucket, dict):
        return []

    history = bucket.get("pnlHistory") or bucket.get("pnl_history") or bucket.get("pnl_history_usd")
    if not isinstance(history, list) or len(history) < 2:
        return []

    values: List[float] = []
    for point in history:
        value = _float_from_history_point(point)
        if value is None:
            continue
        values.append(value)

    if len(values) < 2:
        return []

    return _downsample(values, int(os.getenv("TOP_TRADERS_SPARKLINE_MAX_POINTS", "20")))


def _history_point_ts(point: Any, fallback_index: int = 0) -> int:
    try:
        if isinstance(point, (list, tuple)) and len(point) >= 1:
            return int(float(point[0]))
        if isinstance(point, dict):
            value = (
                point.get("time")
                or point.get("timestamp")
                or point.get("t")
                or point.get("ts")
                or point.get("x")
            )
            if value is not None:
                return int(float(value))
    except Exception:
        pass
    return int(fallback_index)


def _history_point_value(point: Any, keys: Tuple[str, ...]) -> Optional[float]:
    try:
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            return float(str(point[1]).replace("$", "").replace(",", "").strip())
        if isinstance(point, dict):
            value = None
            for key in keys:
                if point.get(key) is not None:
                    value = point.get(key)
                    break
            if value is None:
                return None
            return float(str(value).replace("$", "").replace(",", "").strip())
    except Exception:
        return None
    return None


def _parse_history_points(history: Any, keys: Tuple[str, ...]) -> List[Dict[str, Any]]:
    if not isinstance(history, list):
        return []

    out: List[Dict[str, Any]] = []
    for idx, point in enumerate(history):
        value = _history_point_value(point, keys)
        if value is None:
            continue
        out.append({
            "ts": _history_point_ts(point, idx),
            "value": value,
            "idx": idx,
        })

    out.sort(key=lambda x: (int(x.get("ts") or 0), int(x.get("idx") or 0)))
    return out


def _nearest_value_by_ts(points: List[Dict[str, Any]], ts: int, fallback_index: int = 0) -> Optional[float]:
    if not points:
        return None

    # If timestamps look real, use nearest timestamp.
    if ts and any(int(p.get("ts") or 0) > 100000 for p in points):
        nearest = min(points, key=lambda p: abs(int(p.get("ts") or 0) - int(ts)))
        return float(nearest.get("value"))

    if 0 <= fallback_index < len(points):
        return float(points[fallback_index].get("value"))

    nearest_idx = min(range(len(points)), key=lambda i: abs(i - fallback_index))
    return float(points[nearest_idx].get("value"))


def _downsample_dict_points(points: List[Dict[str, Any]], max_points: int = 80) -> List[Dict[str, Any]]:
    if len(points) <= max_points:
        return points
    if max_points <= 2:
        return [points[0], points[-1]]
    out: List[Dict[str, Any]] = []
    last_index = len(points) - 1
    for i in range(max_points):
        idx = round(i * last_index / (max_points - 1))
        out.append(points[idx])
    return out


def _portfolio_chart_points_from_payload(payload: Any, window: str = "7d") -> List[Dict[str, Any]]:
    bucket = _portfolio_bucket_from_payload(payload, window)
    if not isinstance(bucket, dict):
        return []

    pnl_history = bucket.get("pnlHistory") or bucket.get("pnl_history") or bucket.get("pnl_history_usd")
    av_history = bucket.get("accountValueHistory") or bucket.get("account_value_history") or bucket.get("account_value_usd_history")

    pnl_points = _parse_history_points(
        pnl_history,
        ("pnl", "value", "y", "totalPnl", "cumPnl", "cumulativePnl"),
    )
    av_points = _parse_history_points(
        av_history,
        ("accountValue", "account_value", "value", "y", "equity", "accountEquity"),
    )

    if len(pnl_points) < 2 and len(av_points) < 2:
        return []

    # PnL is the primary x-axis when available; otherwise use account value.
    base_points = pnl_points if len(pnl_points) >= 2 else av_points
    chart: List[Dict[str, Any]] = []

    for idx, point in enumerate(base_points):
        ts = int(point.get("ts") or idx)
        pnl_value = float(point.get("value")) if len(pnl_points) >= 2 else _nearest_value_by_ts(pnl_points, ts, idx)
        av_value = _nearest_value_by_ts(av_points, ts, idx)

        row: Dict[str, Any] = {
            "ts": ts,
            "pnl_usd": pnl_value,
        }

        if av_value is not None and av_value > 0:
            row["account_value"] = av_value
            if pnl_value is not None:
                row["pnl_equity_pct"] = (float(pnl_value) / float(av_value)) * 100.0

        chart.append(row)

    chart = [p for p in chart if p.get("pnl_usd") is not None or p.get("account_value") is not None]
    if len(chart) < 2:
        return []

    return _downsample_dict_points(chart, int(os.getenv("PROFILE_CHART_MAX_POINTS", "80")))


def _attach_portfolio_chart_data(item: Dict[str, Any], address: str, filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach real portfolio chart points for the profile modal.

    Chart series:
    - pnl_usd: Hyperliquid portfolio pnlHistory
    - account_value: Hyperliquid portfolio accountValueHistory
    - pnl_equity_pct: pointwise pnl_usd / account_value * 100

    pnl_equity_pct is intentionally labelled as PnL/equity %, not ROI.
    It is not cashflow-adjusted.
    """
    enabled = os.getenv("PROFILE_PORTFOLIO_CHARTS", "true").lower() in ("1", "true", "yes", "on")
    if not enabled or not address:
        return item

    if item.get("portfolio_chart_points"):
        return item

    window = "1d" if str(filters.get("window") or "").lower() == "1d" else "7d"

    try:
        hl_client = HyperliquidClient()
        payload = hl_client.portfolio(address)
        points = _portfolio_chart_points_from_payload(payload, window)
        if points:
            item["portfolio_chart_points"] = points
            item["portfolio_chart_window"] = window
            item["portfolio_chart_source"] = "hyperliquid_portfolio_pnlHistory_accountValueHistory"

            # Reuse the same real PnL points for mini sparkline if the leaderboard did not already have it.
            if not item.get("pnl_sparkline"):
                item["pnl_sparkline"] = [float(p.get("pnl_usd")) for p in points if p.get("pnl_usd") is not None]
                item["pnl_sparkline_window"] = window
                item["pnl_sparkline_source"] = "hyperliquid_portfolio_pnlHistory"
    except Exception as exc:
        item["portfolio_chart_status"] = f"error: {exc}"

    return item




def _enrich_top_traders_pnl_sparkline(rows: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Add a small real USD PnL trend from Hyperliquid portfolio.pnlHistory.

    No fake points:
    - If portfolio/pnlHistory is missing, the row simply has no sparkline.
    - We do not convert this to %, because deposits/withdrawals can distort %.
    """
    enabled = os.getenv("TOP_TRADERS_SPARKLINE_ENRICH", "true").lower() in ("1", "true", "yes", "on")
    if not enabled or not rows:
        return rows

    window = "1d" if str(filters.get("window") or "").lower() == "1d" else "7d"

    try:
        enrich_limit = int(os.getenv("TOP_TRADERS_SPARKLINE_ENRICH_LIMIT", "50"))
    except Exception:
        enrich_limit = 50
    enrich_limit = max(0, min(enrich_limit, len(rows)))

    try:
        workers = int(os.getenv("TOP_TRADERS_SPARKLINE_WORKERS", "8"))
    except Exception:
        workers = 8
    workers = max(1, min(workers, max(1, enrich_limit)))

    def enrich_one(item: Dict[str, Any]) -> Dict[str, Any]:
        address = str(item.get("address") or "")
        if not address:
            return item

        try:
            hl_client = HyperliquidClient()
            payload = hl_client.portfolio(address)
            sparkline = _pnl_sparkline_from_portfolio_payload(payload, window)
            if sparkline:
                item["pnl_sparkline"] = sparkline
                item["pnl_sparkline_window"] = window
                item["pnl_sparkline_source"] = "hyperliquid_portfolio_pnlHistory"
        except Exception as exc:
            item["pnl_sparkline_status"] = f"error: {exc}"

        return item

    head = rows[:enrich_limit]
    tail = rows[enrich_limit:]
    enriched: List[Optional[Dict[str, Any]]] = [None] * len(head)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(enrich_one, dict(row)): idx for idx, row in enumerate(head)}
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                enriched[idx] = future.result()
            except Exception:
                enriched[idx] = head[idx]

    return [row if row is not None else head[i] for i, row in enumerate(enriched)] + tail




def _enrich_top_traders_account_value(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Lightweight account value enrichment for Top Traders table.

    This only fetches main/default clearinghouseState and only for a capped
    number of visible rows, so it does not change ranking/filter logic.
    """
    enabled = os.getenv("TOP_TRADERS_ACCOUNT_VALUE_ENRICH", "true").lower() in ("1", "true", "yes", "on")
    if not enabled or not rows:
        return rows

    try:
        enrich_limit = int(os.getenv("TOP_TRADERS_ACCOUNT_VALUE_ENRICH_LIMIT", "50"))
    except Exception:
        enrich_limit = 50
    enrich_limit = max(0, min(enrich_limit, len(rows)))

    try:
        workers = int(os.getenv("TOP_TRADERS_ACCOUNT_VALUE_WORKERS", "24"))
    except Exception:
        workers = 24
    workers = max(1, min(workers, max(1, enrich_limit)))

    def enrich_one(item: Dict[str, Any]) -> Dict[str, Any]:
        if item.get("account_value"):
            return item
        address = str(item.get("address") or "")
        if not address:
            return item
        try:
            hl_client = HyperliquidClient()
            hl_state = hl_client.clearinghouse_state(address)
            if hl_state:
                account_value = _extract_account_value_from_state(hl_state)
                if account_value:
                    item["account_value"] = account_value
                    item["account_value_source"] = "hyperliquid_clearinghouseState"
        except Exception as exc:
            item["account_value_status"] = f"error: {exc}"
        return item

    head = rows[:enrich_limit]
    tail = rows[enrich_limit:]
    enriched: List[Optional[Dict[str, Any]]] = [None] * len(head)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(enrich_one, dict(row)): idx for idx, row in enumerate(head)}
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                enriched[idx] = future.result()
            except Exception:
                enriched[idx] = head[idx]

    return [row if row is not None else head[i] for i, row in enumerate(enriched)] + tail



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

    has_tradfi_filter = any(str(row.get("requested_market_type") or row.get("active_market_filter") or "").lower() in ("tradfi", "tradfi_any") for row in rows)
    try:
        default_limit = "250" if has_tradfi_filter else "120"
        enrich_limit = int(os.getenv("TOP_TRADERS_EXPOSURE_ENRICH_LIMIT", default_limit))
    except Exception:
        enrich_limit = 250 if has_tradfi_filter else 120
    enrich_limit = max(0, min(enrich_limit, len(rows)))

    try:
        workers = int(os.getenv("TOP_TRADERS_EXPOSURE_WORKERS", "36"))
    except Exception:
        workers = 12
    workers = max(1, min(workers, max(1, enrich_limit)))

    def enrich_one(item: Dict[str, Any]) -> Dict[str, Any]:
        address = str(item.get("address") or "")
        if not address:
            return item

        try:
            hl_client = HyperliquidClient()
            hl_state, positions, dex_status = _hyperliquid_positions_all_relevant_dexes(hl_client, address, all_mids={})
            if hl_state or positions:
                item["hl_state_status"] = "ok"
                item["dex_state_status"] = dex_status
                item["account_value"] = _extract_account_value_from_state(hl_state or {}) or item.get("account_value", 0)
                if not item.get("account_value"):
                    item["account_value"] = _account_value_from_portfolio_fallback(hl_client, address, "30d")
                    if item.get("account_value"):
                        item["account_value_source"] = "hyperliquid_portfolio"
                item["positions"] = positions
                item["open_positions"] = len(item["positions"])
                item["margin_summary"] = (hl_state or {}).get("marginSummary") or (hl_state or {}).get("crossMarginSummary") or {}
                item = _attach_current_exposure_metrics(item)
            else:
                item["hl_state_status"] = "empty"
                item["positions"] = []
                item["open_positions"] = 0
                item = _attach_current_exposure_metrics(item)
        except Exception as exc:
            item["hl_state_status"] = f"exposure_error: {exc}"

        return item

    head = rows[:enrich_limit]
    tail = rows[enrich_limit:]

    enriched: List[Optional[Dict[str, Any]]] = [None] * len(head)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(enrich_one, dict(row)): idx for idx, row in enumerate(head)}
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                enriched[idx] = future.result()
            except Exception:
                enriched[idx] = head[idx]

    return [row if row is not None else head[i] for i, row in enumerate(enriched)] + tail



def _hydromancer_market_type_candidates(client: HydromancerClient, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    market_type = str(filters.get("market_type") or "all").lower()

    try:
        scan_limit = int(os.getenv("MARKET_TYPE_SCAN_LIMIT", "500"))
    except Exception:
        scan_limit = 500
    scan_limit = max(int(filters.get("limit") or 50), min(scan_limit, 500))

    selected_sort = str(filters.get("sort_by") or "totalPnl")
    scan_sorts: List[str] = []
    for sort_key in (selected_sort, "totalPnl", "volume", "winRate"):
        if sort_key not in scan_sorts:
            scan_sorts.append(sort_key)

    def fetch_sort(sort_key: str) -> Tuple[str, List[Dict[str, Any]]]:
        try:
            rows = client.user_pnl_leaderboard(
                window=filters["window"],
                sort_by=sort_key,
                limit=scan_limit,
                min_trades=filters["min_trades"],
                min_days_active=filters["min_days_active"],
            )
            return sort_key, rows or []
        except Exception as exc:
            print(f"[Hydromancer] market scan failed for sort={sort_key}: {exc}")
            return sort_key, []

    # Fetch sort slices in parallel. This preserves the same candidate universe,
    # but avoids waiting for totalPnl -> volume -> winRate sequentially.
    rows_by_sort: List[Tuple[str, List[Dict[str, Any]]]] = []
    max_workers = min(len(scan_sorts), int(os.getenv("HYDROMANCER_SCAN_WORKERS", "4")))
    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
        future_map = {executor.submit(fetch_sort, sort_key): sort_key for sort_key in scan_sorts}
        tmp: Dict[str, List[Dict[str, Any]]] = {}
        for future in as_completed(future_map):
            sort_key, rows = future.result()
            tmp[sort_key] = rows
        # Keep deterministic interleave order.
        rows_by_sort = [(sort_key, tmp.get(sort_key, [])) for sort_key in scan_sorts]

    out: List[Dict[str, Any]] = []
    seen = set()
    max_len = max((len(rows) for _, rows in rows_by_sort), default=0)

    for i in range(max_len):
        for sort_key, rows in rows_by_sort:
            if i >= len(rows):
                continue
            normalized = normalize_leaderboard_row(rows[i], len(out) + 1)
            address = str(normalized.get("address") or "").lower()
            if not address or address in seen:
                continue
            seen.add(address)
            normalized["leaderboard_window"] = filters["window"]
            normalized["leaderboard_sort_by"] = selected_sort
            normalized["market_scan_source_sort"] = sort_key
            normalized["requested_market_type"] = market_type
            out.append(normalized)

    try:
        max_candidates = int(os.getenv("MARKET_TYPE_MAX_CANDIDATES", "2000" if market_type in ("tradfi", "tradfi_any") else "800"))
    except Exception:
        max_candidates = 300 if market_type in ("tradfi", "tradfi_any") else 180
    max_candidates = max(int(filters.get("limit") or 50), min(max_candidates, 2500))

    return out[:max_candidates]



def list_traders(
    force_refresh: bool = False,
    window: str = "30d",
    sort_by: str = "totalPnl",
    limit: int = 50,
    min_trades: int = 0,
    min_days_active: int = 0,
    market_type: str = "all",
) -> List[Dict[str, Any]]:
    filters = _normalize_leaderboard_filters(window, sort_by, limit, min_trades, min_days_active, market_type)
    cache_key = _leaderboard_cache_key("traders", filters)

    now = time.time()
    cached = _TRADER_LEADERBOARD_CACHE.get(cache_key)
    if (not force_refresh) and cached and (now - float(cached.get("ts", 0))) < _TRADER_LEADERBOARD_CACHE_TTL_SECONDS:
        return cached["data"]

    client = HydromancerClient()
    if client.enabled:
        try:
            if filters.get("market_type") != "all":
                normalized = _hydromancer_market_type_candidates(client, filters)
            else:
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
                row["requested_market_type"] = filters.get("market_type")

            # Current-position enrichment is expensive. Only force it when the
            # Market Type filter needs live positions.
            if filters.get("market_type") != "all":
                normalized = _enrich_top_traders_with_current_exposure(normalized)
            else:
                # For the main leaderboard table, attach Account Value first.
                normalized = _enrich_top_traders_account_value(normalized)

                # v117: Gross Exp. column needs live open-position notionals.
                # This uses the same current exposure path as profile/market filters
                # and is capped by TOP_TRADERS_EXPOSURE_ENRICH_LIMIT if needed.
                normalized = _enrich_top_traders_with_current_exposure(normalized)

            normalized = _apply_local_leaderboard_filters(normalized, filters)

            # Account Value column is visible in the table. For market-type scans,
            # fill missing account values only after filtering, capped to visible rows.
            if filters.get("market_type") != "all":
                normalized = _enrich_top_traders_account_value(normalized)

            for idx, row in enumerate(normalized, start=1):
                row["rank"] = idx

            normalized = _enrich_top_traders_pnl_sparkline(normalized, filters)

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
    market_type: str = "all",
) -> List[Dict[str, Any]]:
    """
    Platform-created/fixed FatBot vault leaderboard.

    The same UI filters are accepted for FatBot Vaults:
    - window controls the HL fills/funding lookback used to compose PnL/volume/funding.
    - sort/min filters are applied locally after vault stats are composed.
    """
    filters = _normalize_leaderboard_filters(window, sort_by, limit, min_trades, min_days_active, market_type)
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


def _find_trader_row_in_leaderboard_caches(address: str) -> Optional[Dict[str, Any]]:
    """
    Find the exact clicked row in existing leaderboard caches, even if it has no
    positions. This is used only to merge table fields such as account_value,
    rank, volume, win_rate, etc. It is NOT used to skip live profile fetching.
    """
    target = str(address or "").lower()
    if not target:
        return None

    for cache_name, cache in [
        ("trader_leaderboard", _TRADER_LEADERBOARD_CACHE),
        ("fatbot_vault", _FATBOT_VAULT_CACHE),
    ]:
        for cache_key, item in list(cache.items()):
            try:
                data = item.get("data") if isinstance(item, dict) else item
                if not isinstance(data, list):
                    continue
                for row in data:
                    if not isinstance(row, dict):
                        continue
                    if str(row.get("address") or "").lower() == target:
                        out = dict(row)
                        out["leaderboard_cache_source"] = f"{cache_name}:{cache_key}"
                        return out
            except Exception:
                continue

    return None


def _merge_cached_row_fields(base: Dict[str, Any], cached: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge non-position leaderboard fields into profile result without overwriting
    real live position data.

    This fixes the case where the table already shows Account Value from a
    lightweight leaderboard enrichment, but the profile live fallback cannot
    fetch positions/account value and would otherwise display a blank value.
    """
    if not isinstance(cached, dict):
        return base

    keep_base_if_present = {
        "positions",
        "open_positions",
        "margin_summary",
        "dex_state_status",
        "hl_state_status",
        "profile_mode",
        "profile_warning",
        "positions_status",
    }

    for key, value in cached.items():
        if key in keep_base_if_present:
            continue
        if value in (None, "", [], {}):
            continue

        current = base.get(key)
        if current in (None, "", [], {}) or (isinstance(current, (int, float)) and float(current) == 0.0):
            base[key] = value

    if cached.get("account_value") and not base.get("account_value"):
        base["account_value"] = cached.get("account_value")
        base["account_value_source"] = cached.get("account_value_source") or "leaderboard_cache"

    base["merged_leaderboard_cache_source"] = cached.get("leaderboard_cache_source")
    return base



def _find_trader_in_leaderboard_caches(address: str) -> Optional[Dict[str, Any]]:
    """
    Find exact clicked row in existing leaderboard caches.

    This prevents a visible TradFi/XYZ row from opening as an empty/0-position
    profile after a profile endpoint re-scan misses the same wallet.
    """
    target = str(address or "").lower()
    if not target:
        return None

    for cache_name, cache in [
        ("trader_leaderboard", _TRADER_LEADERBOARD_CACHE),
        ("fatbot_vault", _FATBOT_VAULT_CACHE),
    ]:
        for cache_key, item in list(cache.items()):
            try:
                data = item.get("data") if isinstance(item, dict) else item
                if not isinstance(data, list):
                    continue
                for row in data:
                    if not isinstance(row, dict):
                        continue
                    if str(row.get("address") or "").lower() == target:
                        # Only use cached leaderboard row as a profile if it actually
                        # contains live positions. Normal Top Traders rows in Market
                        # Type = All deliberately do NOT contain positions, so returning
                        # them here would break normal trader profiles.
                        positions = row.get("positions") or []
                        if not positions:
                            continue

                        out = dict(row)
                        out["history"] = []
                        out["profile_mode"] = "from_existing_leaderboard_cache_with_positions"
                        out["profile_cache_source"] = f"{cache_name}:{cache_key}"
                        out["open_positions"] = len(positions)
                        out = _attach_current_exposure_metrics(out)
                        return out
            except Exception:
                continue

    # Also search server-side snapshot rows persisted in SQLite.
    # This is critical for FatBot Selection, because those rows are not stored in
    # the in-memory Hydromancer leaderboard cache.
    try:
        with get_db() as db:
            rows = db.execute(
                "SELECT payload FROM leaderboard_snapshot_rows ORDER BY rank ASC"
            ).fetchall()
        for row in rows:
            try:
                payload = json.loads(row["payload"])
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            if str(payload.get("address") or "").lower() != target:
                continue
            positions = payload.get("positions") or []
            if not positions:
                continue
            out = dict(payload)
            out["history"] = []
            out["profile_mode"] = "from_server_side_snapshot_with_positions"
            out["profile_cache_source"] = "leaderboard_snapshot_rows"
            out["open_positions"] = len(positions)
            out = _attach_current_exposure_metrics(out)
            return out
    except Exception:
        pass

    return None



def _direct_live_trader_profile(address: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fallback profile path for clicked rows from widened filtered leaderboards.

    A visible TradFi/XYZ row can come from a broad candidate scan. If the profile
    lookup later re-runs a narrower slice and misses that wallet, do not return
    404; build a direct live profile from the address.
    """
    if not HydromancerClient().enabled:
        return None

    cached_metadata_row = _find_trader_row_in_leaderboard_caches(address)

    t: Dict[str, Any] = {
        "address": address,
        "source": "hydromancer",
        "label": "Hydromancer PnL leaderboard",
        "rank": None,
        "total_pnl": 0.0,
        "volume": 0.0,
        "volume_traded": 0.0,
        "win_rate": None,
        "total_trades": 0,
        "account_age_days": 0,
        "positions": [],
        "history": [],
        "profile_mode": "direct_live_fallback",
    }

    try:
        client = HydromancerClient()
        rows = client.user_pnl_leaderboard(
            window=filters["window"],
            sort_by=filters["sort_by"],
            limit=500,
            min_trades=filters["min_trades"],
            min_days_active=filters["min_days_active"],
        )
        for idx, row in enumerate(rows or [], start=1):
            normalized = normalize_leaderboard_row(row, idx)
            if str(normalized.get("address") or "").lower() == str(address).lower():
                t.update(normalized)
                t["rank"] = idx
                break
    except Exception as exc:
        t["hydromancer_profile_status"] = f"merge_error: {exc}"

    try:
        hl_client = HyperliquidClient()
        include_xyz = (
            filters.get("market_type") in ("tradfi", "tradfi_any")
            or os.getenv("PROFILE_INCLUDE_XYZ_DEX", "false").lower() in ("1", "true", "yes", "on")
        )

        if include_xyz:
            hl_state, fresh_positions, dex_status = _hyperliquid_positions_all_relevant_dexes(hl_client, address, all_mids={})
        else:
            hl_state = hl_client.clearinghouse_state(address)
            fresh_positions = _extract_positions_from_state(hl_state or {}, all_mids={}, dex="")
            dex_status = {"dexes_checked": ["main_direct_profile"], "dex_errors": {}}

        t["hl_state_status"] = "ok" if (hl_state or fresh_positions) else "empty"
        t["dex_state_status"] = dex_status
        t["account_value"] = _extract_account_value_from_state(hl_state or {}) or t.get("account_value", 0)
        t["positions"] = fresh_positions or []
        t["open_positions"] = len(t["positions"])
        if not fresh_positions:
            t["positions_status"] = "direct_live_lookup_returned_no_positions"
            t["profile_warning"] = "Direct fallback found no live positions. This is diagnostic, not a confirmed zero-position result."
        t["margin_summary"] = (hl_state or {}).get("marginSummary") or (hl_state or {}).get("crossMarginSummary") or {}
        t = _attach_current_exposure_metrics(t)
    except Exception as exc:
        t["hl_state_status"] = f"error: {exc}"

    return _merge_cached_row_fields(t, cached_metadata_row)


def get_trader(
    address: str,
    window: str = "30d",
    sort_by: str = "totalPnl",
    limit: int = 50,
    min_trades: int = 0,
    min_days_active: int = 0,
    market_type: str = "all",
) -> Optional[Dict[str, Any]]:
    filters = _normalize_leaderboard_filters(window, sort_by, limit, min_trades, min_days_active, market_type)
    profile_cache_key = _leaderboard_cache_key(f"profile:{address.lower()}", filters)

    cached_profile = _profile_cache_get(profile_cache_key)
    if cached_profile is not None:
        return cached_profile

    cached_metadata_row = _find_trader_row_in_leaderboard_caches(address)

    cached_row_profile = _find_trader_in_leaderboard_caches(address)
    if cached_row_profile is not None:
        cached_row_profile = _merge_cached_row_fields(cached_row_profile, cached_metadata_row)
        cached_row_profile = _attach_portfolio_chart_data(cached_row_profile, address, filters)
        return _profile_cache_set(profile_cache_key, cached_row_profile)

    # FatBot vault profiles are platform vaults, even when the address also appears in external leaderboards.
    for vault in list_fatbot_vaults(
        window=filters["window"],
        sort_by=filters["sort_by"],
        limit=filters["limit"],
        min_trades=0,
        min_days_active=0,
        market_type=filters["market_type"],
    ):
        if str(vault.get("address", "")).lower() == address.lower() or str(vault.get("vault_id", "")) == address:
            vault["history"] = []
            vault = _attach_portfolio_chart_data(vault, str(vault.get("address") or address), filters)
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
        market_type=filters["market_type"],
    ):
            if str(t.get("address", "")).lower() == address.lower():
                # Keep positions already attached by the market-type leaderboard enrichment.
                # v67 bug: this was reset to [] before the fresh profile fetch. If the fresh
                # fetch failed or one malformed position raised, the modal showed exposure
                # and "Live Positions > 0" but no rows.
                existing_positions = list(t.get("positions") or [])
                t["positions"] = existing_positions
                t["history"] = []
                t["hl_state_status"] = "not_loaded"

                # Fast profile mode:
                # If the leaderboard row already has enriched live positions/exposure
                # from a market-type scan, return it immediately. This avoids doing
                # another slow allMids + main dex + XYZ dex refresh when opening modal.
                fast_mode = os.getenv("PROFILE_FAST_MODE", "true").lower() in ("1", "true", "yes", "on")
                if fast_mode and existing_positions:
                    t["profile_mode"] = "fast_cached_leaderboard_row_with_positions"
                    t["open_positions"] = len(existing_positions)
                    t = _attach_current_exposure_metrics(t)
                    t = _attach_portfolio_chart_data(t, address, filters)
                    return _profile_cache_set(profile_cache_key, t)

                try:
                    hl_client = HyperliquidClient()

                    # Do not call allMids by default. It is useful for more exact live
                    # prices, but it makes profile opening noticeably slower.
                    all_mids = {}
                    if os.getenv("PROFILE_FETCH_ALL_MIDS", "false").lower() in ("1", "true", "yes", "on"):
                        try:
                            all_mids = hl_client.all_mids()
                        except Exception:
                            all_mids = {}

                    # Only query XYZ/HIP-3 dexes when the profile is opened from an
                    # XYZ/TradFi market filter, or when explicitly enabled.
                    include_xyz = (
                        filters.get("market_type") in ("tradfi", "tradfi_any")
                        or os.getenv("PROFILE_INCLUDE_XYZ_DEX", "false").lower() in ("1", "true", "yes", "on")
                    )

                    if include_xyz:
                        hl_state, fresh_positions, dex_status = _hyperliquid_positions_all_relevant_dexes(hl_client, address, all_mids=all_mids)
                    else:
                        hl_state = hl_client.clearinghouse_state(address)
                        fresh_positions = _extract_positions_from_state(hl_state or {}, all_mids=all_mids, dex="")
                        dex_status = {"dexes_checked": ["main_fast_profile"], "dex_errors": {}}

                    if hl_state or fresh_positions:
                        t["hl_state_status"] = "ok"
                        t["dex_state_status"] = dex_status
                        t["profile_mode"] = "fast_main_only" if not include_xyz else "xyz_dex_profile"
                        t["account_value"] = _extract_account_value_from_state(hl_state or {}) or t.get("account_value", 0)

                        # Avoid portfolio fallback during normal profile opening unless enabled.
                        # Portfolio is slower and account value usually comes from clearinghouseState.
                        if not t.get("account_value") and os.getenv("PROFILE_PORTFOLIO_FALLBACK", "false").lower() in ("1", "true", "yes", "on"):
                            t["account_value"] = _account_value_from_portfolio_fallback(hl_client, address, filters["window"])
                            if t.get("account_value"):
                                t["account_value_source"] = "hyperliquid_portfolio"

                        if fresh_positions:
                            t["positions"] = fresh_positions
                        elif existing_positions:
                            t["positions"] = existing_positions
                            t["positions_status"] = "using_cached_market_filter_positions"
                        else:
                            t["positions"] = []
                            t["positions_status"] = "none_returned"

                        t["open_positions"] = len(t["positions"])
                        t["margin_summary"] = (hl_state or {}).get("marginSummary") or (hl_state or {}).get("crossMarginSummary") or {}
                        t = _attach_current_exposure_metrics(t)
                except Exception as exc:
                    # Do not fail trader profile just because the live state enrichment failed.
                    t["hl_state_status"] = f"error: {exc}"
                    if existing_positions:
                        t["positions"] = existing_positions
                        t["open_positions"] = len(existing_positions)
                        t = _attach_current_exposure_metrics(t)

                t = _merge_cached_row_fields(t, cached_metadata_row)
                t = _attach_portfolio_chart_data(t, address, filters)
                return _profile_cache_set(profile_cache_key, t)

    for vault in list_fatbot_vaults(
        window=filters["window"],
        sort_by=filters["sort_by"],
        limit=filters["limit"],
        min_trades=0,
        min_days_active=0,
        market_type=filters["market_type"],
    ):
        if str(vault.get("address", "")).lower() == address.lower() or str(vault.get("vault_id", "")) == address:
            vault["history"] = []
            return _profile_cache_set(profile_cache_key, vault)

    direct = _direct_live_trader_profile(address, filters)
    if direct:
        direct = _merge_cached_row_fields(direct, cached_metadata_row)
        direct = _attach_portfolio_chart_data(direct, address, filters)
        return _profile_cache_set(profile_cache_key, direct)

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


def _looks_like_clearinghouse_state(value: Any) -> bool:
    return isinstance(value, dict) and (
        isinstance(value.get("assetPositions"), list)
        or isinstance(value.get("positions"), list)
        or isinstance(value.get("marginSummary"), dict)
        or isinstance(value.get("crossMarginSummary"), dict)
    )


def _collect_clearinghouse_states(payload: Any, current_dex: str = "") -> List[Tuple[str, Dict[str, Any]]]:
    """
    Robustly normalize native / HIP-3 / Hydromancer ALL_DEXES response shapes.

    Supported shapes include:
    - normal state dict with assetPositions
    - dict of dex -> state
    - wrappers such as data/result/states/dexStates/clearinghouseStates
    - list entries, including [dex, state] pairs
    """
    out: List[Tuple[str, Dict[str, Any]]] = []

    if payload is None:
        return out

    if isinstance(payload, (list, tuple)):
        if len(payload) == 2 and isinstance(payload[0], str) and isinstance(payload[1], dict):
            return _collect_clearinghouse_states(payload[1], payload[0])
        for item in payload:
            out.extend(_collect_clearinghouse_states(item, current_dex))
        return out

    if not isinstance(payload, dict):
        return out

    dex = str(
        payload.get("dex")
        or payload.get("perpDex")
        or payload.get("dexName")
        or payload.get("name")
        or current_dex
        or ""
    ).strip().lower()

    if _looks_like_clearinghouse_state(payload):
        out.append((dex, payload))

    # Common wrappers first
    for key in ("data", "result", "state", "clearinghouseState"):
        value = payload.get(key)
        if value is not None and value is not payload:
            out.extend(_collect_clearinghouse_states(value, dex))

    # Common ALL_DEXES wrapper shapes
    for key in ("states", "dexStates", "clearinghouseStates", "byDex", "perpDexStates"):
        value = payload.get(key)
        if isinstance(value, dict):
            for dex_key, state in value.items():
                out.extend(_collect_clearinghouse_states(state, str(dex_key).strip().lower()))
        elif isinstance(value, list):
            out.extend(_collect_clearinghouse_states(value, dex))

    return out


def _state_account_value(state: Optional[Dict[str, Any]]) -> float:
    if not isinstance(state, dict):
        return 0.0
    try:
        return _extract_account_value_from_state(state)
    except Exception:
        return 0.0


def _positions_from_state_objects(state_objects: List[Tuple[str, Dict[str, Any]]], all_mids: Optional[Dict[str, float]] = None) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    all_positions: List[Dict[str, Any]] = []
    main_state: Optional[Dict[str, Any]] = None
    dexes_checked: List[str] = []

    # Prefer native/main state as account-value source if present; otherwise
    # choose the state with the largest account value.
    best_state: Optional[Dict[str, Any]] = None
    best_value = -1.0

    for dex_name, state in state_objects:
        label = "main" if not dex_name else dex_name
        if label not in dexes_checked:
            dexes_checked.append(label)

        if not dex_name and main_state is None:
            main_state = state

        value = _state_account_value(state)
        if value > best_value:
            best_value = value
            best_state = state

        all_positions.extend(_extract_positions_from_state(state or {}, all_mids=all_mids or {}, dex=dex_name))

    if main_state is None:
        main_state = best_state

    return main_state, all_positions, {"dexes_checked": dexes_checked, "dex_errors": {}, "state_objects": len(state_objects)}


def _hydromancer_all_dex_state(address: str) -> Optional[Dict[str, Any]]:
    """
    Preferred all-dex state source when Hydromancer is configured.

    Hydromancer docs support dex='ALL_DEXES' for native + all HIP-3 dexes.
    """
    if os.getenv("USE_HYDROMANCER_ALL_DEX_STATE", "true").lower() not in ("1", "true", "yes", "on"):
        return None

    client = HydromancerClient()
    if not client.enabled:
        return None

    return client.clearinghouse_state(address, dex=os.getenv("HYDROMANCER_ALL_DEX_VALUE", "ALL_DEXES"))



def _hyperliquid_positions_all_relevant_dexes(hl_client: HyperliquidClient, address: str, all_mids: Optional[Dict[str, float]] = None) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Fetch positions from all relevant perp dexes.

    Preferred source:
    - Hydromancer clearinghouseState with dex='ALL_DEXES' when API key is configured.

    Fallback source:
    - Hyperliquid native/default clearinghouseState
    - configured HIP-3/XYZ dex clearinghouseState calls in parallel
    """
    # 1) Preferred: Hydromancer ALL_DEXES
    try:
        hm_state = _hydromancer_all_dex_state(address)
        if hm_state:
            state_objects = _collect_clearinghouse_states(hm_state)
            if state_objects:
                main_state, positions, status = _positions_from_state_objects(state_objects, all_mids=all_mids)
                status["source"] = "hydromancer_clearinghouseState_ALL_DEXES"
                if positions or main_state:
                    return main_state, positions, status
            else:
                # Some providers may already return a native-shaped state with no wrappers.
                positions = _extract_positions_from_state(hm_state, all_mids=all_mids or {}, dex="")
                status = {"source": "hydromancer_clearinghouseState_ALL_DEXES", "dexes_checked": ["unknown_shape"], "dex_errors": {}, "state_objects": 0}
                if positions or _state_account_value(hm_state):
                    return hm_state, positions, status
    except Exception as exc:
        hm_error = str(exc)
    else:
        hm_error = None

    # 2) Fallback: official/public HL endpoint per dex
    all_positions: List[Dict[str, Any]] = []
    default_state: Optional[Dict[str, Any]] = None
    dexes = [""] + [d for d in tradfi_dex_names() if d]
    status: Dict[str, Any] = {
        "source": "hyperliquid_clearinghouseState_per_dex",
        "dexes_checked": ["main" if not d else d for d in dexes],
        "dex_errors": {},
    }
    if hm_error:
        status["hydromancer_all_dex_error"] = hm_error

    def fetch_one(dex_name: str) -> Tuple[str, Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
        try:
            state = hl_client.clearinghouse_state(address, dex=dex_name or None)
            positions = _extract_positions_from_state(state or {}, all_mids=all_mids or {}, dex=dex_name) if state else []
            return dex_name, state, positions, None
        except Exception as exc:
            return dex_name, None, [], str(exc)

    workers = min(len(dexes), int(os.getenv("PROFILE_DEX_WORKERS", "6")))
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        future_map = {executor.submit(fetch_one, dex_name): dex_name for dex_name in dexes}
        for future in as_completed(future_map):
            dex_name, state, positions, error = future.result()
            label = "main" if not dex_name else dex_name
            if error:
                status["dex_errors"][label] = error
                continue
            if not dex_name:
                default_state = state
            all_positions.extend(positions)

    return default_state, all_positions, status



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

    # Market Type filter depends on current open-position notionals.
    # v64 bug: these metrics were not attached, so Crypto/TradFi filters returned zero rows.
    row = _attach_market_type_metrics(row)

    return row


def _extract_positions_from_state(state: Dict[str, Any], all_mids: Optional[Dict[str, float]] = None, dex: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = []
    asset_positions = state.get("assetPositions") or state.get("positions") or []
    all_mids = all_mids or {}

    for item in asset_positions:
        try:
            pos = item.get("position") if isinstance(item, dict) and "position" in item else item
            if not isinstance(pos, dict):
                continue

            coin = pos.get("coin") or pos.get("asset") or "?"
            position_dex = str(dex or pos.get("dex") or pos.get("perpDex") or "").strip().lower()
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

            # Prefer current positionValue from clearinghouseState.
            # Fallbacks:
            # - live/mark price * size
            # - entry price * size
            notional = abs(position_value or (szi * price_for_display if price_for_display else 0) or (szi * entry if entry else 0))
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
                "dex": position_dex,
                "qualified_coin": f"{position_dex}:{coin}" if position_dex else coin,
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
        except Exception as exc:
            # Never break the whole profile because one position has a weird/empty field.
            print(f"[Hyperliquid] skipped malformed position: {exc}")
            continue

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

