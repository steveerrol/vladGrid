#!/usr/bin/env python3
"""
Run script for the ES Dec19 25 CME Trading Bot
"""

import uvicorn
from config import Config

if __name__ == "__main__":
    print("🚀 Starting ES Dec19 25 CME Trading Bot")
    print("=" * 50)
    print(f"IBKR Host: {Config.IBKR_HOST}:{Config.IBKR_PORT}")
    print(f"Account ID: {Config.IBKR_ACCOUNT_ID}")
    print(f"Contract: {Config.CONTRACT_SYMBOL} {Config.CONTRACT_MONTH} {Config.CONTRACT_EXCHANGE}")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=Config.LOG_LEVEL.lower()
    )
