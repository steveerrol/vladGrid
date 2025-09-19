#!/usr/bin/env python3
"""
Direct IBKR connection to get bid/ask prices
This is the most reliable method for getting real-time prices
"""

import asyncio
import logging
from ib_insync import IB, Contract
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BidAskPriceGetter:
    """Direct IBKR connection for getting bid/ask prices"""
    
    def __init__(self):
        self.ib = IB()
        self.connected = False
    
    async def connect(self, host='127.0.0.1', port=7497, client_id=1):
        """Connect to IBKR TWS/Gateway"""
        try:
            await self.ib.connectAsync(host, port, clientId=client_id)
            self.connected = True
            logger.info(f"✅ Connected to IBKR at {host}:{port}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to IBKR: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    async def get_es_prices(self, month='20251219'):
        """Get bid/ask prices for ES contract"""
        try:
            if not self.connected:
                raise Exception("Not connected to IBKR")
            
            # Create ES contract
            contract = Contract(
                secType='FUT',
                symbol='ES',
                lastTradeDateOrContractMonth=month,
                exchange='CME',
                currency='USD'
            )
            
            logger.info(f"Getting prices for {contract.symbol} {contract.lastTradeDateOrContractMonth}")
            
            # Request market data
            ticker = self.ib.reqMktData(contract, '', False, False)
            
            # Wait for data (market data can take a moment)
            logger.info("Waiting for market data...")
            await asyncio.sleep(2)
            
            # Get current prices
            prices = {
                'symbol': contract.symbol,
                'month': contract.lastTradeDateOrContractMonth,
                'bid': ticker.bid if ticker.bid > 0 else None,
                'ask': ticker.ask if ticker.ask > 0 else None,
                'last': ticker.last if ticker.last > 0 else None,
                'high': ticker.high if ticker.high > 0 else None,
                'low': ticker.low if ticker.low > 0 else None,
                'volume': ticker.volume if ticker.volume > 0 else None,
                'timestamp': datetime.now().isoformat()
            }
            
            # Calculate spread
            if prices['ask'] and prices['bid']:
                prices['spread'] = prices['ask'] - prices['bid']
                prices['spread_points'] = prices['spread'] * 4  # ES is 0.25 point increments
            
            # Cancel market data request
            self.ib.cancelMktData(contract)
            
            return prices
            
        except Exception as e:
            logger.error(f"Error getting prices: {e}")
            return None
    
    async def get_multiple_contracts(self, months=['20241219', '20250321', '20250620', '20250919', '20251219']):
        """Get prices for multiple ES contracts"""
        try:
            if not self.connected:
                raise Exception("Not connected to IBKR")
            
            all_prices = []
            
            for month in months:
                logger.info(f"Getting prices for ES {month}...")
                prices = await self.get_es_prices(month)
                if prices:
                    all_prices.append(prices)
                    await asyncio.sleep(0.5)  # Small delay between requests
            
            return all_prices
            
        except Exception as e:
            logger.error(f"Error getting multiple contracts: {e}")
            return []
    
    def print_prices(self, prices):
        """Print prices in a nice format"""
        if not prices:
            print("❌ No price data available")
            return
        
        print(f"\n📊 {prices['symbol']} {prices['month']} - {prices['timestamp']}")
        print("="*50)
        print(f"📈 Ask (Buy):  ${prices['ask']}")
        print(f"📉 Bid (Sell): ${prices['bid']}")
        print(f"💰 Last:       ${prices['last']}")
        print(f"📊 High:       ${prices['high']}")
        print(f"📊 Low:        ${prices['low']}")
        print(f"📊 Volume:     {prices['volume']}")
        
        if 'spread' in prices and prices['spread']:
            print(f"📏 Spread:     ${prices['spread']:.2f} ({prices['spread_points']:.1f} points)")

async def main():
    """Main function to demonstrate getting bid/ask prices"""
    print("🎯 Direct IBKR Bid/Ask Price Getter")
    print("="*50)
    
    price_getter = BidAskPriceGetter()
    
    try:
        # Connect to IBKR
        print("1. Connecting to IBKR...")
        await price_getter.connect()
        
        # Get prices for current ES contract
        print("2. Getting current ES prices...")
        prices = await price_getter.get_es_prices('20251219')
        
        if prices:
            price_getter.print_prices(prices)
        else:
            print("❌ Could not get prices")
        
        # Optional: Get prices for multiple contracts
        print("\n3. Getting prices for multiple ES contracts...")
        all_prices = await price_getter.get_multiple_contracts()
        
        if all_prices:
            print(f"\n📊 Multiple ES Contracts:")
            for prices in all_prices:
                price_getter.print_prices(prices)
        else:
            print("❌ Could not get multiple contract prices")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await price_getter.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
