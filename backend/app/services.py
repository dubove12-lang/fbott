import os
import random
import sqlite3
from typing import Any, Dict, List, Optional
from .database import get_db, row_to_dict, rows_to_dicts
from .hydromancer_client import HydromancerClient, HydromancerError, normalize_leaderboard_row


def make_wallet_address() -> str:
    prefix = ''.join(random.choice('0123456789ABCDEF') for _ in range(4))
    suffix = ''.join(random.choice('0123456789ABCDEF') for _ in range(4))
    return f"0xCOPY{prefix}...{suffix}"



def hydromancer_enabled() -> bool:
    return HydromancerClient().enabled


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


def list_traders() -> List[Dict[str, Any]]:
    """
    Production path for the MVP:
    - If HYDROMANCER_API_KEY is set, Smart Traders comes from Hydromancer userPnlLeaderboard.
    - If not set, we fall back to local SQLite seed data so the app still opens.
    """
    client = HydromancerClient()
    if client.enabled:
        try:
            rows = client.user_pnl_leaderboard(
                window=os.getenv("HYDROMANCER_LEADERBOARD_WINDOW", "30d"),
                sort_by=os.getenv("HYDROMANCER_LEADERBOARD_SORT_BY", "totalPnl"),
                limit=int(os.getenv("HYDROMANCER_LEADERBOARD_LIMIT", "50")),
                min_trades=int(os.getenv("HYDROMANCER_LEADERBOARD_MIN_TRADES", "10")),
                min_days_active=int(os.getenv("HYDROMANCER_LEADERBOARD_MIN_DAYS_ACTIVE", "5")),
            )
            normalized = [normalize_leaderboard_row(row, idx + 1) for idx, row in enumerate(rows)]
            return [row for row in normalized if row.get("address")]
        except HydromancerError as exc:
            # Keep MVP usable if API key/rate/shape is wrong.
            print(f"[Hydromancer] leaderboard failed, falling back to SQLite mock data: {exc}")

    with get_db() as db:
        data = rows_to_dicts(db.execute("SELECT * FROM smart_traders ORDER BY score DESC").fetchall())
        for row in data:
            row["source"] = "sqlite_mock"
        return data


def get_trader(address: str) -> Optional[Dict[str, Any]]:
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
    # Find the address in the live leaderboard and enrich with current state if available.
    client = HydromancerClient()
    if client.enabled:
        for t in list_traders():
            if str(t.get("address", "")).lower() == address.lower():
                t["positions"] = []
                state = client.clearinghouse_state(address)
                if state:
                    t["account_value"] = _extract_account_value_from_state(state) or t.get("account_value", 0)
                    t["positions"] = _extract_positions_from_state(state)
                    t["open_positions"] = len(t["positions"])
                t["history"] = []
                return t

    return None


def _extract_account_value_from_state(state: Dict[str, Any]) -> float:
    margin = state.get("marginSummary") or state.get("crossMarginSummary") or {}
    return float(margin.get("accountValue") or margin.get("totalRawUsd") or 0)


def _extract_positions_from_state(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    asset_positions = state.get("assetPositions") or state.get("positions") or []
    for item in asset_positions:
        pos = item.get("position") if isinstance(item, dict) and "position" in item else item
        if not isinstance(pos, dict):
            continue
        coin = pos.get("coin") or pos.get("asset") or "?"
        szi = float(pos.get("szi") or pos.get("size") or 0)
        if szi == 0:
            continue
        entry = float(pos.get("entryPx") or pos.get("entry") or 0)
        mark = float(pos.get("markPx") or pos.get("mark") or 0)
        notional = abs(float(pos.get("positionValue") or pos.get("notional") or (szi * mark if mark else 0)))
        pnl = float(pos.get("unrealizedPnl") or pos.get("pnl") or 0)
        rows.append({
            "coin": coin,
            "side": "Long" if szi > 0 else "Short",
            "notional": notional,
            "entry": entry,
            "mark": mark,
            "pnl": pnl,
            "pnl_pct": 0,
            "leverage": float(pos.get("leverage", {}).get("value", 0)) if isinstance(pos.get("leverage"), dict) else 0,
            "liq_price": float(pos.get("liquidationPx") or 0),
        })
    return rows


def count_wallets_by_mode(mode: str) -> int:
    with get_db() as db:
        if mode == "pool":
            return db.execute("SELECT COUNT(*) c FROM copy_wallets WHERE mode = 'pool'").fetchone()["c"]
        return db.execute("SELECT COUNT(*) c FROM copy_wallets WHERE mode != 'pool'").fetchone()["c"]


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

