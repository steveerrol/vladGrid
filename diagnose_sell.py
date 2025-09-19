#!/usr/bin/env python3
"""
Diagnose sell function issues
"""

import asyncio
import logging
from trading_bot import TradingBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose():
    """Diagnose the sell function"""
    print("🔍 DIAGNOSING SELL FUNCTION")
    print("="*60)
    
    bot = TradingBot()
    
    try:
        # Step 1: Connect
        print("1. Connecting to IBKR...")
        await bot.connect()
        print("✅ Connected successfully")
        
        # Step 2: Check contract
        print("\n2. Checking contract configuration...")
        primary = bot.get_primary_contract()
        if primary:
            print(f"✅ Primary contract: {primary.symbol} {primary.lastTradeDateOrContractMonth}")
        else:
            print("❌ No primary contract found")
            return
        
        # Step 3: Check positions
        print("\n3. Checking positions...")
        positions = await bot.get_positions()
        print(f"Found {len(positions)} positions")
        
        if positions:
            for i, pos in enumerate(positions, 1):
                print(f"  {i}. {pos.symbol}: {pos.quantity} @ ${pos.average_price}")
        else:
            print("No positions found - this is why sell alert is skipped")
            print("To test sell function, you need to have open positions first")
            print("Try buying some contracts first using the buy webhook")
        
        # Step 4: Test close_all_positions
        print("\n4. Testing close_all_positions...")
        result = await bot.close_all_positions()
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.disconnect()

if __name__ == "__main__":
    asyncio.run(diagnose())
