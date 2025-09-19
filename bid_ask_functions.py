#!/usr/bin/env python3
"""
Bid/Ask price functions for your trading bot
"""

import asyncio
from ib_insync import IB, Contract
from datetime import datetime

class BidAskFunctions:
    """Functions to get bid/ask prices directly from IBKR"""
    
    @staticmethod
    async def get_es_bid_ask(month='20251219', host='127.0.0.1', port=7497, client_id=1):
        """
        Get bid/ask prices for ES contract
        
        Args:
            month: Contract month (e.g., '20251219' for DEC 2025)
            host: IBKR host
            port: IBKR port
            client_id: Client ID
        
        Returns:
            dict: {'bid': float, 'ask': float, 'last': float, 'spread': float}
        """
        ib = IB()
        
        try:
            # Connect to IBKR
            await ib.connectAsync(host, port, clientId=client_id)
            
            # Create ES contract
            contract = Contract(
                secType='FUT',
                symbol='ES',
                lastTradeDateOrContractMonth=month,
                exchange='CME',
                currency='USD'
            )
            
            # Request market data
            ticker = ib.reqMktData(contract, '', False, False)
            
            # Wait for data
            await asyncio.sleep(1.5)
            
            # Get prices
            bid = ticker.bid if ticker.bid > 0 else None
            ask = ticker.ask if ticker.ask > 0 else None
            last = ticker.last if ticker.last > 0 else None
            
            # Calculate spread
            spread = None
            if ask and bid:
                spread = ask - bid
            
            # Cancel market data
            ib.cancelMktData(contract)
            
            return {
                'bid': bid,
                'ask': ask,
                'last': last,
                'spread': spread,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting bid/ask: {e}")
            return None
        finally:
            ib.disconnect()
    
    @staticmethod
    async def get_current_es_prices():
        """Get current ES DEC 2025 prices"""
        return await BidAskFunctions.get_es_bid_ask('20251219')
    
    @staticmethod
    def print_prices(prices):
        """Print prices in a nice format"""
        if not prices:
            print("❌ No price data")
            return
        
        print(f"\n📊 ES Prices - {prices['timestamp']}")
        print("="*40)
        print(f"📈 Ask (Buy):  ${prices['ask']}")
        print(f"📉 Bid (Sell): ${prices['bid']}")
        print(f"💰 Last:       ${prices['last']}")
        if prices['spread']:
            print(f"📏 Spread:     ${prices['spread']:.2f}")

# Example usage
async def example_usage():
    """Example of how to use the bid/ask functions"""
    print("🎯 Bid/Ask Functions Example")
    print("="*30)
    
    # Get current ES prices
    prices = await BidAskFunctions.get_current_es_prices()
    
    if prices:
        BidAskFunctions.print_prices(prices)
        
        # Use the prices for trading
        print(f"\n💡 Trading Tips:")
        print(f"   • To BUY: Use ask price ${prices['ask']}")
        print(f"   • To SELL: Use bid price ${prices['bid']}")
        print(f"   • Spread cost: ${prices['spread']:.2f}")
    else:
        print("❌ Could not get prices")

if __name__ == "__main__":
    asyncio.run(example_usage())
