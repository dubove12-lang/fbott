from pydantic import BaseModel, Field
from typing import Optional, List

class Trader(BaseModel):
    address: str
    label: str
    score: int
    pnl_30d: float
    pnl_90d: float
    account_value: float
    open_positions: int
    drawdown: float
    risk: str
    status: str
    gross_exposure: float
    net_exposure: float
    win_rate: float
    avatar: str

class Position(BaseModel):
    coin: str
    side: str
    notional: float
    entry: float
    mark: float
    pnl: float
    pnl_pct: float
    leverage: float
    liq_price: Optional[float] = None

class WalletCreate(BaseModel):
    trader_address: Optional[str] = None
    mode: str = Field(default="single", pattern="^(single|pool)$")
    label: Optional[str] = None

class WalletSettingsPatch(BaseModel):
    multiplier: Optional[float] = Field(default=None, ge=0.1, le=10)
    max_leverage: Optional[float] = Field(default=None, ge=1, le=50)
    max_position_pct: Optional[float] = Field(default=None, ge=1, le=100)
    max_gross_exposure_pct: Optional[float] = Field(default=None, ge=10, le=1000)
    stop_drawdown_pct: Optional[float] = Field(default=None, ge=-95, le=0)
    min_trade_size_usd: Optional[float] = Field(default=None, ge=1)
    slippage_tolerance_pct: Optional[float] = Field(default=None, ge=0.01, le=5)

class PoolCreate(BaseModel):
    name: str = "Pool Copy Wallet"
    vault_name: Optional[str] = None
    trader_addresses: List[str] = Field(min_length=2, max_length=5)
    multiplier: float = Field(default=1.0, ge=0.1, le=10)
