import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the trading bot"""
    
    # IBKR Configuration
    IBKR_ACCOUNT_ID = os.getenv('IBKR_ACCOUNT_ID', '')
    IBKR_HOST = os.getenv('IBKR_HOST', '127.0.0.1')
    IBKR_PORT = int(os.getenv('IBKR_PORT', '7497'))
    IBKR_CLIENT_ID = int(os.getenv('IBKR_CLIENT_ID', '1'))
    
    # Trading Configuration
    CONTRACT_SYMBOL = os.getenv('CONTRACT_SYMBOL', 'ES')
    CONTRACT_MONTH = os.getenv('CONTRACT_MONTH', '20251219')  # ES DEC 2025 contract
    CONTRACT_EXCHANGE = os.getenv('CONTRACT_EXCHANGE', 'CME')
    CONTRACT_CURRENCY = os.getenv('CONTRACT_CURRENCY', 'USD')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'trading_bot.log')
    
    # Webhook Configuration
    SELL_WEBHOOK_PATH = "/ML-2-3-4/sell"
    BUY_WEBHOOK_PATH = "/ML-3-4/buy"
    
    # Order Configuration
    USE_LIMIT_ORDERS = os.getenv('USE_LIMIT_ORDERS', 'false').lower() == 'true'
    BID_ASK_OFFSET = float(os.getenv('BID_ASK_OFFSET', '0.0'))  # Offset from bid/ask in points
