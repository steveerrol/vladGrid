#!/usr/bin/env python3
"""
SPY Stock Trading Module
Handles SPY ETF stock trading
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from ib_insync import IB, Stock, MarketOrder, util
from models import TradeResult
from config import Config

logger = logging.getLogger(__name__)

class SPYStockTrader:
    """SPY Stock Trading Bot using ib-insync"""
    
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.account_id = Config.IBKR_ACCOUNT_ID
        
        # SPY Stock details
        self.stock_symbol = 'SPY'
        self.exchange = 'SMART'
        self.currency = 'USD'
        
        # Fixed quantity for stock trades
        self.fixed_quantity = 5
        
        # Store qualified contract
        self.stock_contract = None
    
    async def connect(self, host: str = None, port: int = None, client_id: int = None):
        """Connect to IBKR TWS/IB Gateway"""
        try:
            # Use config values if not provided
            host = host or Config.IBKR_HOST
            port = port or Config.IBKR_PORT
            client_id = client_id or (Config.IBKR_CLIENT_ID + 20)  # Use different client ID
            
            await self.ib.connectAsync(host, port, clientId=client_id)
            self.connected = True
            logger.info(f"SPY Stock Trader connected to IBKR at {host}:{port}")
            
            # Qualify the stock contract
            await self._qualify_stock_contract()
                
        except Exception as e:
            logger.error(f"Failed to connect SPY Stock Trader to IBKR: {e}")
            self.connected = False
            raise
    
    async def _qualify_stock_contract(self):
        """Qualify the SPY stock contract"""
        try:
            # Define the SPY stock contract
            stock_contract = Stock(
                symbol=self.stock_symbol,
                exchange=self.exchange,
                currency=self.currency
            )
            
            logger.info(f"Qualifying SPY stock contract: {stock_contract.symbol} on {stock_contract.exchange}")
            
            # Qualify the contract
            contracts = await self.ib.qualifyContractsAsync(stock_contract)
            if not contracts:
                raise Exception('SPY stock contract not found or not tradable')
            
            self.stock_contract = contracts[0]
            logger.info(f"✓ SPY stock contract qualified: {self.stock_contract.symbol} {self.stock_contract.exchange}")
            
        except Exception as e:
            logger.error(f"Error qualifying SPY stock contract: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        try:
            if self.connected:
                self.ib.disconnect()
                self.connected = False
                logger.info("SPY Stock Trader disconnected from IBKR")
        except Exception as e:
            logger.error(f"Error disconnecting SPY Stock Trader: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to IBKR"""
        return self.connected and self.ib.isConnected()
    
    async def get_stock_positions(self) -> list:
        """Get current SPY stock positions"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            # Get portfolio items
            portfolio_items = self.ib.portfolio()
            
            # Filter for SPY stock positions
            stock_positions = []
            for item in portfolio_items:
                if (item.contract.symbol == self.stock_symbol and 
                    item.contract.secType == 'STK' and
                    item.position != 0):
                    stock_positions.append({
                        'symbol': item.contract.symbol,
                        'exchange': item.contract.exchange,
                        'quantity': int(item.position),
                        'average_price': getattr(item, 'averageCost', 0.0),
                        'market_value': getattr(item, 'marketValue', 0.0),
                        'unrealized_pnl': getattr(item, 'unrealizedPNL', 0.0)
                    })
            
            logger.info(f"Found {len(stock_positions)} SPY stock positions")
            return stock_positions
            
        except Exception as e:
            logger.error(f"Error getting SPY stock positions: {e}")
            return []
    
    async def buy_stock(self, quantity: int = None) -> TradeResult:
        """Buy SPY stock shares"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            if not self.stock_contract:
                raise Exception("SPY stock contract not qualified")
            
            # Use fixed quantity if not specified
            if quantity is None:
                quantity = self.fixed_quantity
            
            logger.info(f"Placing BUY order for {quantity} SPY stock shares")
            logger.info(f"Contract: {self.stock_contract.symbol} on {self.stock_contract.exchange}")
            
            # Create market order
            order = MarketOrder('BUY', quantity)
            
            # Place the order
            trade = self.ib.placeOrder(self.stock_contract, order)
            
            # Wait for order to be filled
            while not trade.isDone():
                await asyncio.sleep(0.1)
            
            if trade.orderStatus.status == 'Filled':
                filled_quantity = trade.orderStatus.filled
                average_price = trade.orderStatus.avgFillPrice
                
                logger.info(f"✓ SPY stock buy order filled: {filled_quantity} shares at ${average_price}")
                
                return TradeResult(
                    success=True,
                    message=f"Successfully bought {filled_quantity} SPY stock shares at ${average_price}",
                    order_id=trade.order.orderId,
                    filled_quantity=filled_quantity,
                    average_price=average_price
                )
            else:
                error_msg = f"SPY stock buy order not filled: {trade.orderStatus.status}"
                logger.error(error_msg)
                
                return TradeResult(
                    success=False,
                    message=error_msg,
                    order_id=trade.order.orderId
                )
                
        except Exception as e:
            error_msg = f"Error placing SPY stock buy order: {e}"
            logger.error(error_msg)
            return TradeResult(success=False, message=error_msg)
    
    async def sell_all_stock_positions(self) -> Dict[str, Any]:
        """Sell all SPY stock positions"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            logger.info("Starting SPY stock position closure process...")
            
            # Get current positions
            positions = await self.get_stock_positions()
            
            if not positions:
                logger.info("No SPY stock positions found")
                return {
                    "message": "No SPY stock positions to close",
                    "closed_positions": 0,
                    "results": []
                }
            
            logger.info(f"Found {len(positions)} SPY stock positions to close")
            results = []
            total_closed = 0
            
            for position in positions:
                try:
                    if position['quantity'] > 0:  # Long position - sell at market
                        logger.info(f"Closing long SPY stock position: SELL {position['quantity']} shares")
                        
                        order = MarketOrder('SELL', position['quantity'])
                        trade = self.ib.placeOrder(self.stock_contract, order)
                        
                        # Wait for order to be filled
                        while not trade.isDone():
                            await asyncio.sleep(0.1)
                        
                        if trade.orderStatus.status == 'Filled':
                            filled_quantity = trade.orderStatus.filled
                            average_price = trade.orderStatus.avgFillPrice
                            logger.info(f"✓ Successfully closed long SPY stock position: {filled_quantity} shares at ${average_price}")
                            total_closed += filled_quantity
                            results.append({
                                "action": "SELL",
                                "symbol": position['symbol'],
                                "quantity": position['quantity'],
                                "filled": filled_quantity,
                                "price": average_price,
                                "success": True
                            })
                        else:
                            logger.error(f"Failed to close long SPY stock position: {trade.orderStatus.status}")
                            results.append({
                                "action": "SELL",
                                "symbol": position['symbol'],
                                "quantity": position['quantity'],
                                "success": False,
                                "error": trade.orderStatus.status
                            })
                    
                    elif position['quantity'] < 0:  # Short position - buy to close
                        logger.info(f"Closing short SPY stock position: BUY {abs(position['quantity'])} shares")
                        
                        order = MarketOrder('BUY', abs(position['quantity']))
                        trade = self.ib.placeOrder(self.stock_contract, order)
                        
                        # Wait for order to be filled
                        while not trade.isDone():
                            await asyncio.sleep(0.1)
                        
                        if trade.orderStatus.status == 'Filled':
                            filled_quantity = trade.orderStatus.filled
                            average_price = trade.orderStatus.avgFillPrice
                            logger.info(f"✓ Successfully closed short SPY stock position: {filled_quantity} shares at ${average_price}")
                            total_closed += filled_quantity
                            results.append({
                                "action": "BUY_TO_CLOSE",
                                "symbol": position['symbol'],
                                "quantity": abs(position['quantity']),
                                "filled": filled_quantity,
                                "price": average_price,
                                "success": True
                            })
                        else:
                            logger.error(f"Failed to close short SPY stock position: {trade.orderStatus.status}")
                            results.append({
                                "action": "BUY_TO_CLOSE",
                                "symbol": position['symbol'],
                                "quantity": abs(position['quantity']),
                                "success": False,
                                "error": trade.orderStatus.status
                            })
                
                except Exception as e:
                    logger.error(f"Error closing SPY stock position {position}: {e}")
                    results.append({
                        "action": "CLOSE",
                        "symbol": position['symbol'],
                        "quantity": abs(position['quantity']),
                        "success": False,
                        "error": str(e)
                    })
            
            logger.info(f"SPY stock position closure complete: {total_closed} shares closed")
            
            return {
                "message": f"Successfully closed {total_closed} SPY stock shares",
                "closed_positions": total_closed,
                "results": results
            }
            
        except Exception as e:
            error_msg = f"Error closing SPY stock positions: {e}"
            logger.error(error_msg)
            return {
                "message": error_msg,
                "closed_positions": 0,
                "results": []
            }
    
    async def get_stock_market_data(self) -> Optional[Dict[str, Any]]:
        """Get current market data for SPY stock"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            if not self.stock_contract:
                raise Exception("SPY stock contract not qualified")
            
            # Request market data
            ticker = self.ib.reqMktData(self.stock_contract, '', False, False)
            
            # Wait for data
            await asyncio.sleep(1)
            
            # Get bid and ask prices
            bid = ticker.bid if ticker.bid > 0 else None
            ask = ticker.ask if ticker.ask > 0 else None
            last = ticker.last if ticker.last > 0 else None
            
            logger.info(f"SPY stock market data: Bid=${bid}, Ask=${ask}, Last=${last}")
            
            # Cancel market data request
            self.ib.cancelMktData(self.stock_contract)
            
            return {
                'symbol': self.stock_contract.symbol,
                'exchange': self.stock_contract.exchange,
                'bid': bid,
                'ask': ask,
                'last': last,
                'spread': (ask - bid) if (ask and bid) else None
            }
            
        except Exception as e:
            logger.error(f"Error getting SPY stock market data: {e}")
            return None
