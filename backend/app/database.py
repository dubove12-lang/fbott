import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "copytrading.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('PRAGMA journal_mode=WAL')
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def row_to_dict(row):
    return dict(row) if row is not None else None

def rows_to_dicts(rows):
    return [dict(r) for r in rows]

def init_db():
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS smart_traders (
                address TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                score INTEGER NOT NULL,
                pnl_30d REAL NOT NULL,
                pnl_90d REAL NOT NULL,
                account_value REAL NOT NULL,
                open_positions INTEGER NOT NULL,
                drawdown REAL NOT NULL,
                risk TEXT NOT NULL,
                status TEXT NOT NULL,
                gross_exposure REAL NOT NULL,
                net_exposure REAL NOT NULL,
                win_rate REAL NOT NULL,
                avatar TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS trader_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trader_address TEXT NOT NULL,
                coin TEXT NOT NULL,
                side TEXT NOT NULL,
                notional REAL NOT NULL,
                entry REAL NOT NULL,
                mark REAL NOT NULL,
                pnl REAL NOT NULL,
                pnl_pct REAL NOT NULL,
                leverage REAL NOT NULL,
                liq_price REAL,
                FOREIGN KEY (trader_address) REFERENCES smart_traders(address)
            );

            CREATE TABLE IF NOT EXISTS copy_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT NOT NULL UNIQUE,
                label TEXT NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                copied_trader_address TEXT,
                pool_id INTEGER,
                value REAL NOT NULL DEFAULT 0,
                available REAL NOT NULL DEFAULT 0,
                total_pnl REAL NOT NULL DEFAULT 0,
                realized_pnl REAL NOT NULL DEFAULT 0,
                unrealized_pnl REAL NOT NULL DEFAULT 0,
                gross_exposure REAL NOT NULL DEFAULT 0,
                net_exposure REAL NOT NULL DEFAULT 0,
                drift REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                activated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS copy_wallet_settings (
                wallet_id INTEGER PRIMARY KEY,
                copy_mode TEXT NOT NULL DEFAULT 'proportional',
                multiplier REAL NOT NULL DEFAULT 1.0,
                max_leverage REAL NOT NULL DEFAULT 3.0,
                max_position_pct REAL NOT NULL DEFAULT 30.0,
                max_gross_exposure_pct REAL NOT NULL DEFAULT 150.0,
                stop_drawdown_pct REAL NOT NULL DEFAULT -20.0,
                min_trade_size_usd REAL NOT NULL DEFAULT 10.0,
                slippage_tolerance_pct REAL NOT NULL DEFAULT 0.30,
                FOREIGN KEY (wallet_id) REFERENCES copy_wallets(id)
            );

            CREATE TABLE IF NOT EXISTS copy_wallet_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_id INTEGER NOT NULL,
                coin TEXT NOT NULL,
                side TEXT NOT NULL,
                target_notional REAL NOT NULL,
                actual_notional REAL NOT NULL,
                drift_pct REAL NOT NULL,
                pnl REAL NOT NULL,
                pnl_pct REAL NOT NULL,
                FOREIGN KEY (wallet_id) REFERENCES copy_wallets(id)
            );

            CREATE TABLE IF NOT EXISTS copy_pools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'paper',
                multiplier REAL NOT NULL DEFAULT 1.0,
                wallet_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS copy_pool_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_id INTEGER NOT NULL,
                trader_address TEXT NOT NULL,
                weight REAL NOT NULL,
                FOREIGN KEY (pool_id) REFERENCES copy_pools(id),
                FOREIGN KEY (trader_address) REFERENCES smart_traders(address)
            );
            """
        )

def seed_db():
    with get_db() as db:
        exists = db.execute("SELECT COUNT(*) AS c FROM smart_traders").fetchone()["c"]
        if exists:
            return

        traders = [
            ("0x9DB8...7401", "Priority benchmark trader", 92, 31.4, 88.2, 284000, 6, -8.9, "Medium", "Live", 1.42, 0.72, 63.0, "🔥"),
            ("0xb316...8022", "Low drawdown scalper", 89, 24.8, 63.1, 142000, 4, -6.2, "Low", "Live", 0.86, 0.31, 67.0, "🤖"),
            ("0xa5Fd...15FF", "Smooth equity curve", 86, 21.7, 54.6, 491000, 8, -12.4, "Medium", "Live", 1.18, 0.42, 58.0, "🧠"),
            ("0x31DE...13F2", "ETH/SOL specialist", 82, 18.2, 44.3, 93000, 3, -7.1, "Low", "Live", 0.74, 0.18, 61.0, "🦊"),
            ("0x4DEC...27F6", "High beta momentum", 79, 15.9, 39.8, 208000, 5, -14.0, "High", "Live", 1.95, 1.12, 55.0, "⚡"),
            ("0x288E...B336", "Balanced swing trader", 77, 13.1, 32.4, 176000, 4, -9.7, "Medium", "Live", 1.05, -0.22, 57.0, "🐻"),
        ]
        db.executemany(
            """
            INSERT INTO smart_traders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            traders,
        )

        positions = [
            ("0x9DB8...7401", "BTC", "Long", 56800, 101240, 103840, 1840, 3.35, 2.1, 84200),
            ("0x9DB8...7401", "ETH", "Long", 35200, 3460, 3525, 880, 2.56, 1.7, 2940),
            ("0x9DB8...7401", "SOL", "Short", 18400, 157.1, 155.9, 420, 2.33, 1.3, 181.2),
            ("0x9DB8...7401", "HYPE", "Long", 14800, 33.2, 34.1, 410, 2.85, 1.4, 27.8),
            ("0xb316...8022", "BTC", "Long", 21300, 101400, 103840, 520, 2.50, 1.2, 89100),
            ("0xb316...8022", "FARTCOIN", "Short", 7800, 1.18, 1.14, 264, 3.50, 1.1, 1.44),
            ("0xa5Fd...15FF", "ETH", "Long", 74200, 3402, 3525, 2680, 3.72, 1.8, 2850),
            ("0xa5Fd...15FF", "HYPE", "Long", 36000, 31.8, 34.1, 2460, 7.01, 1.6, 25.0),
        ]
        db.executemany(
            """
            INSERT INTO trader_positions
            (trader_address, coin, side, notional, entry, mark, pnl, pnl_pct, leverage, liq_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            positions,
        )

        db.execute(
            """
            INSERT INTO copy_wallets
            (wallet_address, label, mode, status, copied_trader_address, value, available, total_pnl, realized_pnl, unrealized_pnl, gross_exposure, net_exposure, drift, activated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ("0xCOPY...A91", "Copy Wallet #1", "single", "active", "0x9DB8...7401", 12482.10, 2840.22, 1284.22, 560.02, 724.20, 1.42, 0.72, 1.8),
        )
        wallet_id = db.execute("SELECT id FROM copy_wallets WHERE wallet_address = ?", ("0xCOPY...A91",)).fetchone()["id"]
        db.execute(
            """
            INSERT INTO copy_wallet_settings
            (wallet_id, multiplier, max_leverage, max_position_pct, max_gross_exposure_pct, stop_drawdown_pct, min_trade_size_usd, slippage_tolerance_pct)
            VALUES (?, 1.0, 3.0, 30.0, 150.0, -20.0, 10.0, 0.30)
            """,
            (wallet_id,),
        )
        wallet_positions = [
            (wallet_id, "BTC", "Long", 2840, 2802, -1.3, 184.20, 6.58),
            (wallet_id, "ETH", "Long", 1760, 1791, 1.8, 88.72, 5.07),
            (wallet_id, "SOL", "Short", 920, 906, -1.5, -21.40, -2.31),
            (wallet_id, "HYPE", "Long", 740, 744, 0.5, 41.18, 5.56),
        ]
        db.executemany(
            """
            INSERT INTO copy_wallet_positions
            (wallet_id, coin, side, target_notional, actual_notional, drift_pct, pnl, pnl_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            wallet_positions,
        )

        db.execute("INSERT INTO copy_pools (name, status, multiplier) VALUES ('Pool Copy Wallet #1', 'paper', 1.0)")
        pool_id = db.execute("SELECT id FROM copy_pools WHERE name = 'Pool Copy Wallet #1'").fetchone()["id"]
        db.executemany(
            "INSERT INTO copy_pool_members (pool_id, trader_address, weight) VALUES (?, ?, ?)",
            [(pool_id, "0x9DB8...7401", 33.33), (pool_id, "0xb316...8022", 33.33), (pool_id, "0xa5Fd...15FF", 33.34)],
        )
