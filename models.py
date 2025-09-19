from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AlertRequest(BaseModel):
    """Model for TradingView alert requests"""
    symbol: Optional[str] = None
    action: Optional[str] = None
    price: Optional[float] = None
    timestamp: Optional[str] = None
    message: Optional[str] = None

class Position(BaseModel):
    """Model for position information"""
    symbol: str
    quantity: int
    average_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float

class TradeResult(BaseModel):
    """Model for trade execution results"""
    success: bool
    message: str
    order_id: Optional[int] = None
    filled_quantity: Optional[int] = None
    average_price: Optional[float] = None
    timestamp: datetime = datetime.now()

class AccountInfo(BaseModel):
    """Model for account information"""
    account_id: str
    buying_power: float
    net_liquidation: float
    total_cash_value: float
    gross_position_value: float
