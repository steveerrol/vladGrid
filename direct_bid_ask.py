#!/usr/bin/env python3
"""
Example: Get bid/ask prices directly from IBKR
"""

import asyncio
import logging
from ib_insync import IB, Contract

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_direct_bid_ask():
    """Get bid/ask prices directly from IBKR"""
    print("📊 Direct IBKR Bid/Ask Prices")
    print("="*40)
    
    ib = IB()
    
    try:
        # Connect to IBKR
        print("1. Connecting to IBKR...")
        await ib.connectAsync('127.0.0.1', 7497, clientId=1)
        print("✅ Connected")
        
        # Create ES contract
        contract = Contract(
            secType='FUT',
            symbol='ES',
            lastTradeDateOrContractMonth='20251219',
            exchange='CME',
            currency='USD'
        )
        
        print(f"2. Contract: {contract.symbol} {contract.lastTradeDateOrContractMonth}")
        
        # Request market data
        print("3. Requesting market data...")
        ticker = ib.reqMktData(contract, '', False, False)
        
        # Wait for data
        print("4. Waiting for market data...")
        await asyncio.sleep(2)
        
        # Get prices
        print(f"✅ Market Data:")
        print(f"   📈 Ask: ${ticker.ask}")
        print(f"   📉 Bid: ${ticker.bid}")
        print(f"   💰 Last: ${ticker.last}")
        print(f"   📊 High: ${ticker.high}")
        print(f"   📊 Low: ${ticker.low}")
        print(f"   📊 Volume: {ticker.volume}")
        
        # Calculate spread
        if ticker.ask and ticker.bid:
            spread = ticker.ask - ticker.bid
            print(f"   📏 Spread: ${spread:.2f}")
        
        # Cancel market data request
        ib.cancelMktData(contract)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await ib.disconnect()

if __name__ == "__main__":
    asyncio.run(get_direct_bid_ask())
