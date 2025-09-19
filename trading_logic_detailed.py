#!/usr/bin/env python3
"""
Detailed Trading Logic - Buy and Sell Process
This shows exactly how the bot executes trades
"""

import asyncio
import logging
from ib_insync import IB, Contract, MarketOrder, LimitOrder
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetailedTradingLogic:
    """Detailed explanation of buy/sell logic"""
    
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.contract = None
    
    async def connect(self):
        """Connect to IBKR"""
        try:
            await self.ib.connectAsync('127.0.0.1', 7497, clientId=1)
            self.connected = True
            logger.info("✅ Connected to IBKR")
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
    
    def setup_contract(self):
        """Setup ES contract"""
        self.contract = Contract(
            secType='FUT',
            symbol='ES',
            lastTradeDateOrContractMonth='20251219',  # ES DEC 2025
            exchange='CME',
            currency='USD'
        )
        logger.info(f"Contract setup: {self.contract.symbol} {self.contract.lastTradeDateOrContractMonth}")
    
    async def get_market_data(self):
        """Get current market data (bid/ask)"""
        try:
            logger.info("📊 Getting market data...")
            
            # Request market data
            ticker = self.ib.reqMktData(self.contract, '', False, False)
            
            # Wait for data
            await asyncio.sleep(1.5)
            
            # Get prices
            bid = ticker.bid if ticker.bid > 0 else None
            ask = ticker.ask if ticker.ask > 0 else None
            last = ticker.last if ticker.last > 0 else None
            
            logger.info(f"Market data received:")
            logger.info(f"  Bid: ${bid}")
            logger.info(f"  Ask: ${ask}")
            logger.info(f"  Last: ${last}")
            
            # Cancel market data
            self.ib.cancelMktData(self.contract)
            
            return {
                'bid': bid,
                'ask': ask,
                'last': last
            }
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None
    
    async def buy_contracts_detailed(self, quantity):
        """Detailed buy logic with step-by-step explanation"""
        logger.info("="*60)
        logger.info("🛒 BUY PROCESS - Step by Step")
        logger.info("="*60)
        
        try:
            # Step 1: Validate connection
            logger.info("Step 1: Validating connection...")
            if not self.connected:
                raise Exception("Not connected to IBKR")
            logger.info("✅ Connected to IBKR")
            
            # Step 2: Get market data
            logger.info("Step 2: Getting current market data...")
            market_data = await self.get_market_data()
            if not market_data:
                raise Exception("Could not get market data")
            
            # Step 3: Determine buy price
            logger.info("Step 3: Determining buy price...")
            buy_price = market_data['ask']  # Use ask price to buy
            logger.info(f"✅ Will buy at ask price: ${buy_price}")
            
            # Step 4: Create limit order
            logger.info("Step 4: Creating limit order...")
            order = LimitOrder('BUY', quantity, buy_price)
            logger.info(f"✅ Order created: BUY {quantity} contracts at ${buy_price}")
            
            # Step 5: Place order
            logger.info("Step 5: Placing order with IBKR...")
            trade = self.ib.placeOrder(self.contract, order)
            logger.info(f"✅ Order placed, ID: {trade.order.orderId}")
            
            # Step 6: Wait for execution
            logger.info("Step 6: Waiting for order execution...")
            timeout = 30  # 30 seconds timeout
            waited = 0
            
            while not trade.isDone() and waited < timeout:
                await asyncio.sleep(0.1)
                waited += 0.1
                logger.info(f"  Waiting... ({waited:.1f}s) Status: {trade.orderStatus.status}")
            
            # Step 7: Check execution result
            logger.info("Step 7: Checking execution result...")
            if trade.isDone():
                if trade.orderStatus.status == 'Filled':
                    filled_qty = trade.orderStatus.filled
                    avg_price = trade.orderStatus.avgFillPrice
                    logger.info(f"✅ ORDER FILLED!")
                    logger.info(f"  Filled: {filled_qty} contracts")
                    logger.info(f"  Average Price: ${avg_price}")
                    return {
                        'success': True,
                        'filled_quantity': filled_qty,
                        'average_price': avg_price,
                        'order_id': trade.order.orderId
                    }
                else:
                    logger.error(f"❌ Order not filled: {trade.orderStatus.status}")
                    return {
                        'success': False,
                        'error': trade.orderStatus.status,
                        'order_id': trade.order.orderId
                    }
            else:
                logger.error(f"❌ Order timeout after {timeout} seconds")
                return {
                    'success': False,
                    'error': 'Timeout',
                    'order_id': trade.order.orderId
                }
                
        except Exception as e:
            logger.error(f"❌ Buy process failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def sell_contracts_detailed(self, quantity):
        """Detailed sell logic with step-by-step explanation"""
        logger.info("="*60)
        logger.info("💰 SELL PROCESS - Step by Step")
        logger.info("="*60)
        
        try:
            # Step 1: Validate connection
            logger.info("Step 1: Validating connection...")
            if not self.connected:
                raise Exception("Not connected to IBKR")
            logger.info("✅ Connected to IBKR")
            
            # Step 2: Get market data
            logger.info("Step 2: Getting current market data...")
            market_data = await self.get_market_data()
            if not market_data:
                raise Exception("Could not get market data")
            
            # Step 3: Determine sell price
            logger.info("Step 3: Determining sell price...")
            sell_price = market_data['bid']  # Use bid price to sell
            logger.info(f"✅ Will sell at bid price: ${sell_price}")
            
            # Step 4: Create limit order
            logger.info("Step 4: Creating limit order...")
            order = LimitOrder('SELL', quantity, sell_price)
            logger.info(f"✅ Order created: SELL {quantity} contracts at ${sell_price}")
            
            # Step 5: Place order
            logger.info("Step 5: Placing order with IBKR...")
            trade = self.ib.placeOrder(self.contract, order)
            logger.info(f"✅ Order placed, ID: {trade.order.orderId}")
            
            # Step 6: Wait for execution
            logger.info("Step 6: Waiting for order execution...")
            timeout = 30  # 30 seconds timeout
            waited = 0
            
            while not trade.isDone() and waited < timeout:
                await asyncio.sleep(0.1)
                waited += 0.1
                logger.info(f"  Waiting... ({waited:.1f}s) Status: {trade.orderStatus.status}")
            
            # Step 7: Check execution result
            logger.info("Step 7: Checking execution result...")
            if trade.isDone():
                if trade.orderStatus.status == 'Filled':
                    filled_qty = trade.orderStatus.filled
                    avg_price = trade.orderStatus.avgFillPrice
                    logger.info(f"✅ ORDER FILLED!")
                    logger.info(f"  Filled: {filled_qty} contracts")
                    logger.info(f"  Average Price: ${avg_price}")
                    return {
                        'success': True,
                        'filled_quantity': filled_qty,
                        'average_price': avg_price,
                        'order_id': trade.order.orderId
                    }
                else:
                    logger.error(f"❌ Order not filled: {trade.orderStatus.status}")
                    return {
                        'success': False,
                        'error': trade.orderStatus.status,
                        'order_id': trade.order.orderId
                    }
            else:
                logger.error(f"❌ Order timeout after {timeout} seconds")
                return {
                    'success': False,
                    'error': 'Timeout',
                    'order_id': trade.order.orderId
                }
                
        except Exception as e:
            logger.error(f"❌ Sell process failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_positions_detailed(self):
        """Detailed position checking logic"""
        logger.info("="*60)
        logger.info("📊 POSITION CHECK - Step by Step")
        logger.info("="*60)
        
        try:
            # Step 1: Get portfolio items
            logger.info("Step 1: Getting portfolio items...")
            portfolio_items = self.ib.portfolio()
            logger.info(f"✅ Found {len(portfolio_items)} portfolio items")
            
            # Step 2: Filter ES positions
            logger.info("Step 2: Filtering ES positions...")
            es_positions = []
            for item in portfolio_items:
                if item.contract.symbol == 'ES' and item.position != 0:
                    es_positions.append(item)
                    logger.info(f"  ES Position: {item.position} contracts")
            
            logger.info(f"✅ Found {len(es_positions)} ES positions")
            
            # Step 3: Return position data
            return es_positions
            
        except Exception as e:
            logger.error(f"❌ Position check failed: {e}")
            return []
    
    async def close_all_positions_detailed(self):
        """Detailed position closing logic"""
        logger.info("="*60)
        logger.info("🚪 CLOSE ALL POSITIONS - Step by Step")
        logger.info("="*60)
        
        try:
            # Step 1: Get current positions
            logger.info("Step 1: Getting current positions...")
            positions = await self.get_positions_detailed()
            
            if not positions:
                logger.info("✅ No positions to close")
                return {'closed': 0, 'results': []}
            
            # Step 2: Get market data
            logger.info("Step 2: Getting market data for closing...")
            market_data = await self.get_market_data()
            if not market_data:
                raise Exception("Could not get market data")
            
            # Step 3: Close each position
            logger.info("Step 3: Closing positions...")
            results = []
            total_closed = 0
            
            for i, pos in enumerate(positions, 1):
                logger.info(f"  Closing position {i}/{len(positions)}: {pos.position} contracts")
                
                if pos.position > 0:  # Long position - sell
                    logger.info(f"    Long position: SELL {pos.position} at ${market_data['bid']}")
                    result = await self.sell_contracts_detailed(pos.position)
                    results.append({'action': 'SELL', 'result': result})
                    if result['success']:
                        total_closed += result['filled_quantity']
                
                elif pos.position < 0:  # Short position - buy to close
                    logger.info(f"    Short position: BUY {abs(pos.position)} at ${market_data['ask']}")
                    result = await self.buy_contracts_detailed(abs(pos.position))
                    results.append({'action': 'BUY_TO_CLOSE', 'result': result})
                    if result['success']:
                        total_closed += result['filled_quantity']
            
            logger.info(f"✅ Closed {total_closed} contracts total")
            return {'closed': total_closed, 'results': results}
            
        except Exception as e:
            logger.error(f"❌ Close positions failed: {e}")
            return {'closed': 0, 'results': [], 'error': str(e)}

async def demo_trading_logic():
    """Demonstrate the detailed trading logic"""
    print("🎯 Detailed Trading Logic Demo")
    print("="*50)
    
    trader = DetailedTradingLogic()
    
    try:
        # Connect
        await trader.connect()
        trader.setup_contract()
        
        # Show current positions
        positions = await trader.get_positions_detailed()
        
        # Demo buy (if no positions)
        if not positions:
            print("\n🛒 DEMO: Buying 1 contract...")
            buy_result = await trader.buy_contracts_detailed(1)
            print(f"Buy result: {buy_result}")
        
        # Demo sell (if we have positions)
        positions = await trader.get_positions_detailed()
        if positions:
            print("\n💰 DEMO: Selling 1 contract...")
            sell_result = await trader.sell_contracts_detailed(1)
            print(f"Sell result: {sell_result}")
        
        # Demo close all
        print("\n🚪 DEMO: Closing all positions...")
        close_result = await trader.close_all_positions_detailed()
        print(f"Close result: {close_result}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        await trader.disconnect()

if __name__ == "__main__":
    asyncio.run(demo_trading_logic())
