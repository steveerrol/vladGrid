#!/usr/bin/env python3
"""
Example: How to get bid/ask prices in the trading bot
"""

import asyncio
import logging
from trading_bot import TradingBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_bid_ask_prices():
    """Get current bid/ask prices"""
    print("📊 Getting Bid/Ask Prices")
    print("="*40)
    
    bot = TradingBot()
    
    try:
        # Connect to IBKR
        print("1. Connecting to IBKR...")
        await bot.connect()
        print("✅ Connected")
        
        # Get primary contract
        contract = bot.get_primary_contract()
        if not contract:
            print("❌ No contract found")
            return
        
        print(f"2. Contract: {contract.symbol} {contract.lastTradeDateOrContractMonth}")
        
        # Method 1: Use the built-in get_market_data function
        print("3. Getting market data...")
        market_data = await bot.get_market_data(contract)
        
        if market_data:
            print(f"✅ Current Prices:")
            print(f"   📈 Ask (Buy): ${market_data['ask']}")
            print(f"   📉 Bid (Sell): ${market_data['bid']}")
            print(f"   💰 Last: ${market_data['last']}")
            
            # Calculate spread
            if market_data['ask'] and market_data['bid']:
                spread = market_data['ask'] - market_data['bid']
                print(f"   📏 Spread: ${spread:.2f}")
        else:
            print("❌ Could not get market data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.disconnect()

if __name__ == "__main__":
    asyncio.run(get_bid_ask_prices())
