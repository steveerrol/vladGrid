#!/usr/bin/env python3
"""
Demo script showing bid/ask functionality
"""

import asyncio
import logging
from trading_bot import TradingBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_bid_ask():
    """Demonstrate bid/ask trading"""
    print("🎯 ES Trading Bot - Bid/Ask Demo")
    print("="*50)
    
    bot = TradingBot()
    
    try:
        # Connect to IBKR
        print("1. Connecting to IBKR...")
        await bot.connect()
        print("✅ Connected to IBKR")
        
        # Get primary contract
        contract = bot.get_primary_contract()
        if not contract:
            print("❌ No primary contract found")
            return
        
        print(f"2. Contract: {contract.symbol} {contract.lastTradeDateOrContractMonth}")
        
        # Get market data (bid/ask prices)
        print("3. Getting current market data...")
        market_data = await bot.get_market_data(contract)
        
        if market_data:
            print(f"✅ Current Market Prices:")
            print(f"   📈 Ask (Buy): ${market_data['ask']}")
            print(f"   📉 Bid (Sell): ${market_data['bid']}")
            print(f"   💰 Last: ${market_data['last']}")
            
            # Show how to use bid/ask
            print(f"\n4. How to use Bid/Ask:")
            print(f"   • To BUY: Use ask price (${market_data['ask']})")
            print(f"   • To SELL: Use bid price (${market_data['bid']})")
            
            print(f"\n5. Available Functions:")
            print(f"   • buy_contracts_limit(3) - Buy 3 at ask price")
            print(f"   • sell_contracts_limit(3) - Sell 3 at bid price")
            print(f"   • buy_contracts_limit(3, 6700.0) - Buy 3 at $6700")
            print(f"   • sell_contracts_limit(3, 6695.0) - Sell 3 at $6695")
            
            print(f"\n6. Webhook URLs for TradingView:")
            print(f"   • Buy at Ask: https://94d501344003.ngrok-free.app/ML-3-4/buy-limit")
            print(f"   • Sell at Bid: https://94d501344003.ngrok-free.app/ML-2-3-4/sell-limit")
            
        else:
            print("❌ Could not get market data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.disconnect()

if __name__ == "__main__":
    asyncio.run(demo_bid_ask())
