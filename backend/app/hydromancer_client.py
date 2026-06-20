import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests


class HydromancerError(RuntimeError):
    pass


class HydromancerClient:
    """
    Minimal Hydromancer REST client for the MVP.

    Hydromancer REST uses:
      POST https://api.hydromancer.xyz/info
      Authorization: Bearer <API_KEY>

    We keep the API key server-side only. The frontend never sees it.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("HYDROMANCER_API_KEY", "").strip()
        self.base_url = os.getenv("HYDROMANCER_BASE_URL", "https://api.hydromancer.xyz").rstrip("/")
        self.timeout = float(os.getenv("HYDROMANCER_TIMEOUT", "20"))
        self.dex = os.getenv("HYDROMANCER_DEX", "").strip() or None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _post_info(self, payload: Dict[str, Any]) -> Any:
        if not self.enabled:
            raise HydromancerError("HYDROMANCER_API_KEY is missing")

        url = f"{self.base_url}/info"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)

        if response.status_code >= 400:
            body = response.text[:500]
            raise HydromancerError(f"Hydromancer {response.status_code}: {body}")

        try:
            return response.json()
        except Exception as exc:
            raise HydromancerError(f"Hydromancer returned non-JSON response: {exc}") from exc

    def user_pnl_leaderboard(
        self,
        window: str = "30d",
        sort_by: str = "totalPnl",
        limit: int = 50,
        min_trades: int = 10,
        min_days_active: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Calls Hydromancer userPnlLeaderboard.

        Docs indicate:
          type: userPnlLeaderboard
          sortBy: totalPnl / winRate / volume
          limit, minTrades, minDaysActive quality filters

        Some Hydromancer fields may differ by plan/version, so we normalize response shapes below.
        """
        payload: Dict[str, Any] = {
            "type": "userPnlLeaderboard",
            "window": window,
            "sortBy": sort_by,
            "limit": limit,
            "minTrades": min_trades,
            "minDaysActive": min_days_active,
        }
        if self.dex:
            payload["dex"] = self.dex

        data = self._post_info(payload)
        return self._extract_rows(data)

    def clearinghouse_state(self, user: str) -> Optional[Dict[str, Any]]:
        """
        Optional enrichment. If Hydromancer supports clearinghouseState through /info,
        this gives current account value and open positions.
        """
        payload: Dict[str, Any] = {"type": "clearinghouseState", "user": user}
        if self.dex:
            payload["dex"] = self.dex
        try:
            data = self._post_info(payload)
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    @staticmethod
    def _extract_rows(data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]

        if isinstance(data, dict):
            for key in ("users", "leaders", "leaderboard", "rows", "data", "result", "items", "pnlLeaderboard", "userPnlLeaderboard"):
                value = data.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]

            # Some APIs wrap one more level: {"data": {"rows": [...]}}
            for outer in ("data", "result"):
                nested = data.get(outer)
                if isinstance(nested, dict):
                    for key in ("users", "leaders", "leaderboard", "rows", "items"):
                        value = nested.get(key)
                        if isinstance(value, list):
                            return [x for x in value if isinstance(x, dict)]

        return []


def first_present(row: Dict[str, Any], keys: Tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return default


def as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        if isinstance(value, str):
            value = value.replace("$", "").replace(",", "").replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(as_float(value, default))
    except Exception:
        return default


def normalize_leaderboard_row(row: Dict[str, Any], rank: int) -> Dict[str, Any]:
    """
    Real userPnlLeaderboard fields observed from Hydromancer:
      user, totalPnl, volumeTraded, totalTrades, winRate, totalFees,
      totalFunding, daysActive, accountAgeDays, humanScore, tradedPairs

    winRate is returned as a decimal ratio, e.g. 0.7857 = 78.57%.
    Most monetary values are string decimals and are converted to float.
    """
    address = first_present(
        row,
        (
            "user",
            "address",
            "wallet",
            "walletAddress",
            "account",
            "userAddress",
            "trader",
            "accountAddress",
        ),
        "",
    )

    total_pnl = as_float(first_present(row, ("totalPnl", "totalPNL", "pnl", "realizedPnl", "realized_pnl", "profit", "totalProfit", "cumPnl", "cumulativePnl"), 0))
    volume = as_float(first_present(row, ("volumeTraded", "volume", "tradedVolume", "totalVolume", "notionalVolume"), 0))
    fees = as_float(first_present(row, ("totalFees", "fees", "totalFee"), 0))
    funding = as_float(first_present(row, ("totalFunding", "funding", "fundingPnl"), 0))
    trades = as_int(first_present(row, ("totalTrades", "trades", "numTrades", "tradeCount", "nTrades"), 0))
    days_active = as_int(first_present(row, ("daysActive", "activeDays"), 0))
    account_age_days = as_int(first_present(row, ("accountAgeDays", "ageDays"), 0))
    human_score = as_float(first_present(row, ("humanScore",), 0))
    win_rate_raw = as_float(first_present(row, ("winRate", "win_rate", "winrate"), 0))
    win_rate_pct = win_rate_raw * 100 if 0 <= win_rate_raw <= 1 else win_rate_raw
    traded_pairs = first_present(row, ("tradedPairs", "pairs", "coins", "markets"), []) or []
    if not isinstance(traded_pairs, list):
        traded_pairs = []

    # Keep score only as rank helper for legacy frontend; do not present it as recommendation logic.
    score = max(1, min(99, int(100 - rank * 1.7)))

    # We keep risk as neutral placeholder for legacy schema compatibility only.
    risk = "External"

    roi_proxy = 0.0
    # No account value is returned by userPnlLeaderboard, so ROI cannot be computed from this endpoint alone.
    # We keep pnl_30d as total_pnl for sorting/legacy UI compatibility when selected window is 30d.
    pnl_window = total_pnl

    return {
        "address": str(address),
        "label": "Hydromancer PnL leaderboard",
        "score": score,
        "rank": rank,
        "pnl_30d": pnl_window,
        "pnl_90d": pnl_window,
        "account_value": as_float(first_present(row, ("accountValue", "account_value", "equity", "marginSummaryAccountValue"), 0)),
        "open_positions": as_int(first_present(row, ("openPositions", "open_positions", "positions"), 0)),
        "drawdown": as_float(first_present(row, ("drawdown", "maxDrawdown", "max_drawdown"), 0)),
        "risk": risk,
        "win_rate": win_rate_pct,
        "gross_exposure": as_float(first_present(row, ("grossExposure", "gross_exposure"), 0)),
        "net_exposure": as_float(first_present(row, ("netExposure", "net_exposure"), 0)),
        "total_pnl": total_pnl,
        "volume": volume,
        "volume_traded": volume,
        "fees": fees,
        "total_fees": fees,
        "funding": funding,
        "total_funding": funding,
        "trades": trades,
        "total_trades": trades,
        "days_active": days_active,
        "account_age_days": account_age_days,
        "human_score": human_score,
        "traded_pairs": traded_pairs,
        "traded_pairs_count": len(traded_pairs),
        "source": "hydromancer",
        "raw": row,
    }
