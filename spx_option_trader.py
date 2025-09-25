#!/usr/bin/env python3
"""
SPX Option Trading Module
Handles SPXW options trading for specific contracts
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from ib_insync import IB, Option, MarketOrder, util
from models import TradeResult
from config import Config

logger = logging.getLogger(__name__)

class SPXOptionTrader:
    """SPX Option Trading Bot using ib-insync"""
    
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.account_id = Config.IBKR_ACCOUNT_ID
        
        # SPXW Option contract details
        self.option_symbol = 'SPXW'
        self.expiration = '20251010'  # 10 Oct 2025
        self.strike = 6675
        self.right = 'C'  # Call option
        self.exchange = 'SMART'
        self.currency = 'USD'
        self.trading_class = 'SPXW'
        
        # Fixed quantity for option trades
        self.fixed_quantity = 1
        
        # Store qualified contract
        self.option_contract = None
    
    async def connect(self, host: str = None, port: int = None, client_id: int = None):
        """Connect to IBKR TWS/IB Gateway"""
        try:
            # Use config values if not provided
            host = host or Config.IBKR_HOST
            port = port or Config.IBKR_PORT
            client_id = client_id or (Config.IBKR_CLIENT_ID + 10)  # Use different client ID
            
            await self.ib.connectAsync(host, port, clientId=client_id)
            self.connected = True
            logger.info(f"SPX Option Trader connected to IBKR at {host}:{port}")
            
            # Qualify the option contract
            await self._qualify_option_contract()
                
        except Exception as e:
            logger.error(f"Failed to connect SPX Option Trader to IBKR: {e}")
            self.connected = False
            raise
    
    async def _qualify_option_contract(self):
        """Qualify the SPX option contract"""
        try:
            # Define the SPX option contract
            option_contract = Option(
                symbol=self.option_symbol,
                lastTradeDateOrContractMonth=self.expiration,
                strike=self.strike,
                right=self.right,
                exchange=self.exchange,
                currency=self.currency,
                tradingClass=self.trading_class
            )
            
            logger.info(f"Qualifying SPX option contract: {option_contract.symbol} {option_contract.strike} {option_contract.right} {option_contract.lastTradeDateOrContractMonth}")
            
            # Qualify the contract
            contracts = await self.ib.qualifyContractsAsync(option_contract)
            if not contracts:
                raise Exception('SPX option contract not found or not tradable')
            
            self.option_contract = contracts[0]
            logger.info(f"✓ SPX option contract qualified: {self.option_contract.localSymbol}")
            
        except Exception as e:
            logger.error(f"Error qualifying SPX option contract: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        try:
            if self.connected:
                self.ib.disconnect()
                self.connected = False
                logger.info("SPX Option Trader disconnected from IBKR")
        except Exception as e:
            logger.error(f"Error disconnecting SPX Option Trader: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to IBKR"""
        return self.connected and self.ib.isConnected()
    
    async def get_option_positions(self) -> list:
        """Get current SPX option positions"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            # Get portfolio items
            portfolio_items = self.ib.portfolio()
            
            # Filter for SPX option positions
            option_positions = []
            for item in portfolio_items:
                if (item.contract.symbol == self.option_symbol and 
                    item.contract.secType == 'OPT' and
                    item.position != 0):
                    option_positions.append({
                        'symbol': item.contract.symbol,
                        'strike': item.contract.strike,
                        'right': item.contract.right,
                        'expiration': item.contract.lastTradeDateOrContractMonth,
                        'quantity': int(item.position),
                        'average_price': getattr(item, 'averageCost', 0.0),
                        'market_value': getattr(item, 'marketValue', 0.0),
                        'unrealized_pnl': getattr(item, 'unrealizedPNL', 0.0)
                    })
            
            logger.info(f"Found {len(option_positions)} SPX option positions")
            return option_positions
            
        except Exception as e:
            logger.error(f"Error getting SPX option positions: {e}")
            return []
    
    async def buy_option(self, quantity: int = None) -> TradeResult:
        """Buy SPX option contracts"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            if not self.option_contract:
                raise Exception("SPX option contract not qualified")
            
            # Use fixed quantity if not specified
            if quantity is None:
                quantity = self.fixed_quantity
            
            logger.info(f"Placing BUY order for {quantity} SPX option contracts")
            logger.info(f"Contract: {self.option_contract.symbol} {self.option_contract.strike} {self.option_contract.right} {self.option_contract.lastTradeDateOrContractMonth}")
            
            # Create market order
            order = MarketOrder('BUY', quantity)
            
            # Place the order
            trade = self.ib.placeOrder(self.option_contract, order)
            
            # Wait for order to be filled
            while not trade.isDone():
                await asyncio.sleep(0.1)
            
            if trade.orderStatus.status == 'Filled':
                filled_quantity = trade.orderStatus.filled
                average_price = trade.orderStatus.avgFillPrice
                
                logger.info(f"✓ SPX option buy order filled: {filled_quantity} contracts at ${average_price}")
                
                return TradeResult(
                    success=True,
                    message=f"Successfully bought {filled_quantity} SPX option contracts at ${average_price}",
                    order_id=trade.order.orderId,
                    filled_quantity=filled_quantity,
                    average_price=average_price
                )
            else:
                error_msg = f"SPX option buy order not filled: {trade.orderStatus.status}"
                logger.error(error_msg)
                
                return TradeResult(
                    success=False,
                    message=error_msg,
                    order_id=trade.order.orderId
                )
                
        except Exception as e:
            error_msg = f"Error placing SPX option buy order: {e}"
            logger.error(error_msg)
            return TradeResult(success=False, message=error_msg)
    
    async def sell_all_option_positions(self) -> Dict[str, Any]:
        """Sell all SPX option positions"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            logger.info("Starting SPX option position closure process...")
            
            # Get current positions
            positions = await self.get_option_positions()
            
            if not positions:
                logger.info("No SPX option positions found")
                return {
                    "message": "No SPX option positions to close",
                    "closed_positions": 0,
                    "results": []
                }
            
            logger.info(f"Found {len(positions)} SPX option positions to close")
            results = []
            total_closed = 0
            
            for position in positions:
                try:
                    # Create contract for this specific position
                    contract = Option(
                        symbol=position['symbol'],
                        lastTradeDateOrContractMonth=position['expiration'],
                        strike=position['strike'],
                        right=position['right'],
                        exchange=self.exchange,
                        currency=self.currency,
                        tradingClass=self.trading_class
                    )
                    
                    # Qualify the contract
                    qualified_contracts = await self.ib.qualifyContractsAsync(contract)
                    if not qualified_contracts:
                        logger.error(f"Could not qualify contract for position: {position}")
                        continue
                    
                    qualified_contract = qualified_contracts[0]
                    
                    if position['quantity'] > 0:  # Long position - sell at market
                        logger.info(f"Closing long SPX option position: SELL {position['quantity']} contracts")
                        
                        order = MarketOrder('SELL', position['quantity'])
                        trade = self.ib.placeOrder(qualified_contract, order)
                        
                        # Wait for order to be filled
                        while not trade.isDone():
                            await asyncio.sleep(0.1)
                        
                        if trade.orderStatus.status == 'Filled':
                            filled_quantity = trade.orderStatus.filled
                            average_price = trade.orderStatus.avgFillPrice
                            logger.info(f"✓ Successfully closed long SPX option position: {filled_quantity} contracts at ${average_price}")
                            total_closed += filled_quantity
                            results.append({
                                "action": "SELL",
                                "symbol": position['symbol'],
                                "strike": position['strike'],
                                "right": position['right'],
                                "quantity": position['quantity'],
                                "filled": filled_quantity,
                                "price": average_price,
                                "success": True
                            })
                        else:
                            logger.error(f"Failed to close long SPX option position: {trade.orderStatus.status}")
                            results.append({
                                "action": "SELL",
                                "symbol": position['symbol'],
                                "strike": position['strike'],
                                "right": position['right'],
                                "quantity": position['quantity'],
                                "success": False,
                                "error": trade.orderStatus.status
                            })
                    
                    elif position['quantity'] < 0:  # Short position - buy to close
                        logger.info(f"Closing short SPX option position: BUY {abs(position['quantity'])} contracts")
                        
                        order = MarketOrder('BUY', abs(position['quantity']))
                        trade = self.ib.placeOrder(qualified_contract, order)
                        
                        # Wait for order to be filled
                        while not trade.isDone():
                            await asyncio.sleep(0.1)
                        
                        if trade.orderStatus.status == 'Filled':
                            filled_quantity = trade.orderStatus.filled
                            average_price = trade.orderStatus.avgFillPrice
                            logger.info(f"✓ Successfully closed short SPX option position: {filled_quantity} contracts at ${average_price}")
                            total_closed += filled_quantity
                            results.append({
                                "action": "BUY_TO_CLOSE",
                                "symbol": position['symbol'],
                                "strike": position['strike'],
                                "right": position['right'],
                                "quantity": abs(position['quantity']),
                                "filled": filled_quantity,
                                "price": average_price,
                                "success": True
                            })
                        else:
                            logger.error(f"Failed to close short SPX option position: {trade.orderStatus.status}")
                            results.append({
                                "action": "BUY_TO_CLOSE",
                                "symbol": position['symbol'],
                                "strike": position['strike'],
                                "right": position['right'],
                                "quantity": abs(position['quantity']),
                                "success": False,
                                "error": trade.orderStatus.status
                            })
                
                except Exception as e:
                    logger.error(f"Error closing SPX option position {position}: {e}")
                    results.append({
                        "action": "CLOSE",
                        "symbol": position['symbol'],
                        "strike": position['strike'],
                        "right": position['right'],
                        "quantity": abs(position['quantity']),
                        "success": False,
                        "error": str(e)
                    })
            
            logger.info(f"SPX option position closure complete: {total_closed} contracts closed")
            
            return {
                "message": f"Successfully closed {total_closed} SPX option contracts",
                "closed_positions": total_closed,
                "results": results
            }
            
        except Exception as e:
            error_msg = f"Error closing SPX option positions: {e}"
            logger.error(error_msg)
            return {
                "message": error_msg,
                "closed_positions": 0,
                "results": []
            }
    
    async def get_option_market_data(self) -> Optional[Dict[str, Any]]:
        """Get current market data for the SPX option"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            if not self.option_contract:
                raise Exception("SPX option contract not qualified")
            
            # Request market data
            ticker = self.ib.reqMktData(self.option_contract, '', False, False)
            
            # Wait for data
            await asyncio.sleep(1)
            
            # Get bid and ask prices
            bid = ticker.bid if ticker.bid > 0 else None
            ask = ticker.ask if ticker.ask > 0 else None
            last = ticker.last if ticker.last > 0 else None
            
            logger.info(f"SPX option market data: Bid=${bid}, Ask=${ask}, Last=${last}")
            
            # Cancel market data request
            self.ib.cancelMktData(self.option_contract)
            
            return {
                'symbol': self.option_contract.symbol,
                'strike': self.option_contract.strike,
                'right': self.option_contract.right,
                'expiration': self.option_contract.lastTradeDateOrContractMonth,
                'bid': bid,
                'ask': ask,
                'last': last,
                'spread': (ask - bid) if (ask and bid) else None
            }
            
        except Exception as e:
            logger.error(f"Error getting SPX option market data: {e}")
            return None
