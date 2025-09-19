import asyncio
import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from ib_insync import IB, Contract, MarketOrder, LimitOrder, util
from ib_insync.objects import Position as IBPosition
from models import Position, TradeResult, AccountInfo
from config import Config

logger = logging.getLogger(__name__)

class TradingBot:
    """ES CME Future Trading Bot using ib-insync"""
    
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.account_id = Config.IBKR_ACCOUNT_ID
        
        # Load selected contracts
        self.contracts = self.load_selected_contracts()
        
        # Contract multiplier for ES futures
        self.contract_multiplier = 50
    
    def load_selected_contracts(self):
        """Load selected contracts from file or use default"""
        try:
            # Try to load from selected_contracts.txt
            contracts = []
            with open('selected_contracts.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(',')
                        if len(parts) >= 4:
                            contract = Contract(
                                secType='FUT',
                                symbol=parts[0],
                                lastTradeDateOrContractMonth=parts[1],
                                exchange=parts[2],
                                currency=parts[3]
                            )
                            if len(parts) > 4:
                                contract.multiplier = parts[4]
                            contracts.append(contract)
            
            if contracts:
                logger.info(f"Loaded {len(contracts)} selected contracts")
                return contracts
        except FileNotFoundError:
            logger.info("No selected_contracts.txt found, using default contract")
        except Exception as e:
            logger.error(f"Error loading selected contracts: {e}")
        
        # Fallback to default contract
        default_contract = Contract(
            secType='FUT',
            symbol=Config.CONTRACT_SYMBOL,
            lastTradeDateOrContractMonth=Config.CONTRACT_MONTH,
            exchange=Config.CONTRACT_EXCHANGE,
            currency=Config.CONTRACT_CURRENCY
        )
        return [default_contract]
    
    def get_primary_contract(self):
        """Get the primary contract for trading"""
        return self.contracts[0] if self.contracts else None
        
    async def connect(self, host: str = None, port: int = None, client_id: int = None):
        """Connect to IBKR TWS/IB Gateway"""
        try:
            # Use config values if not provided
            host = host or Config.IBKR_HOST
            port = port or Config.IBKR_PORT
            client_id = client_id or Config.IBKR_CLIENT_ID
            
            await self.ib.connectAsync(host, port, clientId=client_id)
            self.connected = True
            logger.info(f"Connected to IBKR at {host}:{port}")
            
            # Qualify the contracts
            try:
                qualified_contracts = []
                for contract in self.contracts:
                    try:
                        qualified = await self.ib.qualifyContractsAsync(contract)
                        if qualified:
                            qualified_contracts.extend(qualified)
                            logger.info(f"Qualified contract: {contract.symbol} {contract.lastTradeDateOrContractMonth}")
                        else:
                            logger.warning(f"Could not qualify {contract.symbol} {contract.lastTradeDateOrContractMonth}")
                    except Exception as e:
                        logger.warning(f"Error qualifying {contract.symbol} {contract.lastTradeDateOrContractMonth}: {e}")
                
                if qualified_contracts:
                    self.contracts = qualified_contracts
                    logger.info(f"Successfully qualified {len(qualified_contracts)} contracts")
                else:
                    # Try to find available ES contracts
                    logger.warning("Could not qualify any selected contracts, searching for available ES contracts...")
                    
                    search_contract = Contract(
                        secType='FUT',
                        symbol='ES',
                        exchange='CME',
                        currency='USD'
                    )
                    
                    search_results = await self.ib.qualifyContractsAsync(search_contract)
                    if search_results:
                        self.contracts = search_results
                        logger.info(f"Using {len(search_results)} available ES contracts")
                    else:
                        raise Exception("No ES contracts available")
                        
            except Exception as e:
                logger.error(f"Contract qualification error: {e}")
                # Continue without qualification - some brokers work without it
                logger.warning("Continuing without contract qualification")
                
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        try:
            if self.connected:
                self.ib.disconnect()
                self.connected = False
                logger.info("Disconnected from IBKR")
        except Exception as e:
            logger.error(f"Error disconnecting from IBKR: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to IBKR"""
        return self.connected and self.ib.isConnected()
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            # Get positions from IBKR
            ib_positions = self.ib.positions()
            logger.info(f"Raw IBKR positions count: {len(ib_positions)}")
            
            # Also get portfolio items (which might contain position data)
            portfolio_items = self.ib.portfolio()
            logger.info(f"Portfolio items count: {len(portfolio_items)}")
            
            # Log all positions for debugging
            for i, pos in enumerate(ib_positions):
                logger.info(f"Position {i+1}: {pos.contract.symbol} {pos.contract.secType} {pos.contract.exchange} {pos.contract.lastTradeDateOrContractMonth} - Qty: {pos.position}")
            
            # Log portfolio items
            for i, item in enumerate(portfolio_items):
                logger.info(f"Portfolio {i+1}: {item.contract.symbol} {item.contract.secType} {item.contract.exchange} {item.contract.lastTradeDateOrContractMonth} - Qty: {item.position}")
            
            positions = []
            
            # Check portfolio items first (they have more complete data)
            for item in portfolio_items:
                if item.position != 0:  # Only non-zero positions
                    # Check if it's an ES contract
                    is_es = item.contract.symbol == 'ES'
                    
                    if is_es:
                        position = Position(
                            symbol=item.contract.symbol,
                            quantity=int(item.position),
                            average_price=getattr(item, 'averageCost', 0.0),
                            market_value=getattr(item, 'marketValue', 0.0),
                            unrealized_pnl=getattr(item, 'unrealizedPNL', 0.0),
                            realized_pnl=getattr(item, 'realizedPNL', 0.0)
                        )
                        positions.append(position)
                        logger.info(f"✅ Added ES position from portfolio: {position.symbol} {position.quantity} @ ${position.average_price}")
            
            # If no positions found in portfolio, check regular positions
            if not positions:
                logger.info("No ES positions found in portfolio, checking regular positions...")
                for pos in ib_positions:
                    if pos.position != 0:  # Only non-zero positions
                        # Check if it's an ES contract
                        is_es = pos.contract.symbol == 'ES'
                        
                        if is_es:
                            position = Position(
                                symbol=pos.contract.symbol,
                                quantity=int(pos.position),
                                average_price=getattr(pos, 'averageCost', 0.0),
                                market_value=getattr(pos, 'marketValue', 0.0),
                                unrealized_pnl=getattr(pos, 'unrealizedPNL', 0.0),
                                realized_pnl=getattr(pos, 'realizedPNL', 0.0)
                            )
                            positions.append(position)
                            logger.info(f"✅ Added ES position from positions: {position.symbol} {position.quantity} @ ${position.average_price}")
            
            logger.info(f"Retrieved {len(positions)} ES positions")
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            # Get account summary
            account_values = self.ib.accountSummary()
            
            account_info = {}
            for value in account_values:
                account_info[value.tag] = float(value.value)
            
            return AccountInfo(
                account_id=self.account_id,
                buying_power=account_info.get('BuyingPower', 0.0),
                net_liquidation=account_info.get('NetLiquidation', 0.0),
                total_cash_value=account_info.get('TotalCashValue', 0.0),
                gross_position_value=account_info.get('GrossPositionValue', 0.0)
            )
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    async def get_market_data(self, contract):
        """Get current market data (bid/ask) for a contract"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            # Request market data
            ticker = self.ib.reqMktData(contract, '', False, False)
            
            # Wait for data
            await asyncio.sleep(1)
            
            # Get bid and ask prices
            bid = ticker.bid if ticker.bid > 0 else None
            ask = ticker.ask if ticker.ask > 0 else None
            last = ticker.last if ticker.last > 0 else None
            
            logger.info(f"Market data for {contract.symbol}: Bid=${bid}, Ask=${ask}, Last=${last}")
            
            # Cancel market data request
            self.ib.cancelMktData(contract)
            
            return {
                'bid': bid,
                'ask': ask,
                'last': last
            }
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None

    async def buy_contracts_limit(self, quantity: int, price: float = None, use_bid: bool = False) -> TradeResult:
        """Buy contracts with limit order at specified price or ask price"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            primary_contract = self.get_primary_contract()
            if not primary_contract:
                raise Exception("No contracts available")
            
            # Ensure contract has exchange specified
            if not primary_contract.exchange:
                primary_contract.exchange = 'CME'
                logger.info(f"Set exchange to CME for primary contract: {primary_contract.symbol}")
            
            # Get market data if price not specified
            if price is None:
                market_data = await self.get_market_data(primary_contract)
                if market_data:
                    if use_bid and market_data['bid']:
                        price = market_data['bid']
                        logger.info(f"Using bid price for buy: ${price}")
                    elif not use_bid and market_data['ask']:
                        price = market_data['ask']
                        logger.info(f"Using ask price for buy: ${price}")
                    else:
                        raise Exception("Could not get market price")
                else:
                    raise Exception("Could not get market data")
            
            logger.info(f"Placing buy limit order for {quantity} {primary_contract.symbol} at ${price}")
            
            # Create limit order
            order = LimitOrder('BUY', quantity, price)
            
            # Place the order
            trade = self.ib.placeOrder(primary_contract, order)
            
            # Wait for order to be filled
            while not trade.isDone():
                await asyncio.sleep(0.1)
            
            if trade.orderStatus.status == 'Filled':
                filled_quantity = trade.orderStatus.filled
                average_price = trade.orderStatus.avgFillPrice
                
                logger.info(f"Order filled: {filled_quantity} contracts at ${average_price}")
                
                return TradeResult(
                    success=True,
                    message=f"Successfully bought {filled_quantity} contracts at ${average_price}",
                    order_id=trade.order.orderId,
                    filled_quantity=filled_quantity,
                    average_price=average_price
                )
            else:
                error_msg = f"Order not filled: {trade.orderStatus.status}"
                logger.error(error_msg)
                
                return TradeResult(
                    success=False,
                    message=error_msg,
                    order_id=trade.order.orderId
                )
                
        except Exception as e:
            error_msg = f"Error placing buy limit order: {e}"
            logger.error(error_msg)
            return TradeResult(success=False, message=error_msg)

    async def sell_contracts_limit(self, quantity: int, price: float = None, use_ask: bool = False) -> TradeResult:
        """Sell contracts with limit order at specified price or bid price"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            primary_contract = self.get_primary_contract()
            if not primary_contract:
                raise Exception("No contracts available")
            
            # Ensure contract has exchange specified
            if not primary_contract.exchange:
                primary_contract.exchange = 'CME'
                logger.info(f"Set exchange to CME for primary contract: {primary_contract.symbol}")
            
            # Get market data if price not specified
            if price is None:
                market_data = await self.get_market_data(primary_contract)
                if market_data:
                    if use_ask and market_data['ask']:
                        price = market_data['ask']
                        logger.info(f"Using ask price for sell: ${price}")
                    elif not use_ask and market_data['bid']:
                        price = market_data['bid']
                        logger.info(f"Using bid price for sell: ${price}")
                    else:
                        raise Exception("Could not get market price")
                else:
                    raise Exception("Could not get market data")
            
            logger.info(f"Placing sell limit order for {quantity} {primary_contract.symbol} at ${price}")
            
            # Create limit order
            order = LimitOrder('SELL', quantity, price)
            
            # Place the order
            trade = self.ib.placeOrder(primary_contract, order)
            
            # Wait for order to be filled
            while not trade.isDone():
                await asyncio.sleep(0.1)
            
            if trade.orderStatus.status == 'Filled':
                filled_quantity = trade.orderStatus.filled
                average_price = trade.orderStatus.avgFillPrice
                
                logger.info(f"Order filled: {filled_quantity} contracts at ${average_price}")
                
                return TradeResult(
                    success=True,
                    message=f"Successfully sold {filled_quantity} contracts at ${average_price}",
                    order_id=trade.order.orderId,
                    filled_quantity=filled_quantity,
                    average_price=average_price
                )
            else:
                error_msg = f"Order not filled: {trade.orderStatus.status}"
                logger.error(error_msg)
                
                return TradeResult(
                    success=False,
                    message=error_msg,
                    order_id=trade.order.orderId
                )
                
        except Exception as e:
            error_msg = f"Error placing sell limit order: {e}"
            logger.error(error_msg)
            return TradeResult(success=False, message=error_msg)

    async def buy_contracts(self, quantity: int) -> TradeResult:
        """Buy specified number of contracts"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            primary_contract = self.get_primary_contract()
            if not primary_contract:
                raise Exception("No contracts available")
            
            # Ensure contract has exchange specified
            if not primary_contract.exchange:
                primary_contract.exchange = 'CME'
                logger.info(f"Set exchange to CME for primary contract: {primary_contract.symbol}")
            
            logger.info(f"Placing buy order for {quantity} {primary_contract.symbol} {primary_contract.lastTradeDateOrContractMonth} contracts")
            
            # Create market order
            order = MarketOrder('BUY', quantity)
            
            # Place the order
            trade = self.ib.placeOrder(primary_contract, order)
            
            # Wait for order to be filled
            while not trade.isDone():
                await asyncio.sleep(0.1)
            
            if trade.orderStatus.status == 'Filled':
                filled_quantity = trade.orderStatus.filled
                average_price = trade.orderStatus.avgFillPrice
                
                logger.info(f"Order filled: {filled_quantity} contracts at ${average_price}")
                
                return TradeResult(
                    success=True,
                    message=f"Successfully bought {filled_quantity} contracts at ${average_price}",
                    order_id=trade.order.orderId,
                    filled_quantity=filled_quantity,
                    average_price=average_price
                )
            else:
                error_msg = f"Order not filled: {trade.orderStatus.status}"
                logger.error(error_msg)
                
                return TradeResult(
                    success=False,
                    message=error_msg,
                    order_id=trade.order.orderId
                )
                
        except Exception as e:
            error_msg = f"Error placing buy order: {e}"
            logger.error(error_msg)
            return TradeResult(success=False, message=error_msg)
    
    async def sell_contracts(self, quantity: int) -> TradeResult:
        """Sell specified number of contracts"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            primary_contract = self.get_primary_contract()
            if not primary_contract:
                raise Exception("No contracts available")
            
            # Ensure contract has exchange specified
            if not primary_contract.exchange:
                primary_contract.exchange = 'CME'
                logger.info(f"Set exchange to CME for primary contract: {primary_contract.symbol}")
            
            logger.info(f"Placing sell order for {quantity} {primary_contract.symbol} {primary_contract.lastTradeDateOrContractMonth} contracts")
            
            # Create market order
            order = MarketOrder('SELL', quantity)
            
            # Place the order
            trade = self.ib.placeOrder(primary_contract, order)
            
            # Wait for order to be filled
            while not trade.isDone():
                await asyncio.sleep(0.1)
            
            if trade.orderStatus.status == 'Filled':
                filled_quantity = trade.orderStatus.filled
                average_price = trade.orderStatus.avgFillPrice
                
                logger.info(f"Order filled: {filled_quantity} contracts at ${average_price}")
                
                return TradeResult(
                    success=True,
                    message=f"Successfully sold {filled_quantity} contracts at ${average_price}",
                    order_id=trade.order.orderId,
                    filled_quantity=filled_quantity,
                    average_price=average_price
                )
            else:
                error_msg = f"Order not filled: {trade.orderStatus.status}"
                logger.error(error_msg)
                
                return TradeResult(
                    success=False,
                    message=error_msg,
                    order_id=trade.order.orderId
                )
                
        except Exception as e:
            error_msg = f"Error placing sell order: {e}"
            logger.error(error_msg)
            return TradeResult(success=False, message=error_msg)
    
    async def close_all_positions_force(self) -> Dict[str, Any]:
        """Force close ALL positions regardless of symbol"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            logger.info("Starting FORCE close_all_positions process...")
            
            # Get portfolio items (more reliable for position data)
            portfolio_items = self.ib.portfolio()
            logger.info(f"Portfolio items count: {len(portfolio_items)}")
            
            # Log all portfolio items for debugging
            for i, item in enumerate(portfolio_items):
                logger.info(f"Portfolio item {i+1}: {item.contract.symbol} {item.contract.secType} {item.contract.exchange} - Qty: {item.position}")
                logger.info(f"  Average cost: {getattr(item, 'averageCost', 'N/A')}")
                logger.info(f"  Market value: {getattr(item, 'marketValue', 'N/A')}")
            
            # Filter only non-zero positions
            non_zero_positions = [item for item in portfolio_items if item.position != 0]
            logger.info(f"Non-zero positions count: {len(non_zero_positions)}")
            
            if not non_zero_positions:
                logger.info("No non-zero positions found")
                return {
                    "message": "No positions to close",
                    "closed_positions": 0,
                    "results": []
                }
            
            logger.info(f"Found {len(non_zero_positions)} non-zero positions to close")
            results = []
            total_closed = 0
            
            for i, pos in enumerate(non_zero_positions, 1):
                logger.info(f"Processing position {i}/{len(non_zero_positions)}: {pos.contract.symbol} {pos.position}")
                
                if pos.position > 0:  # Long position - sell at market price
                    try:
                        logger.info(f"Closing long position: SELL {pos.position} {pos.contract.symbol} contracts at market price")

                        # Ensure contract has exchange specified
                        contract = pos.contract
                        if not contract.exchange:
                            contract.exchange = 'CME'  # Default to CME for ES futures
                            logger.info(f"Set exchange to CME for contract: {contract.symbol}")

                        # Use market order for immediate execution
                        order = MarketOrder('SELL', int(pos.position))
                        trade = self.ib.placeOrder(contract, order)
                    
                        # Wait for order to be filled (with timeout)
                        timeout = 30  # 30 seconds timeout
                        waited = 0
                        while not trade.isDone() and waited < timeout:
                            await asyncio.sleep(0.1)
                            waited += 0.1
                        
                        if trade.isDone():
                            if trade.orderStatus.status == 'Filled':
                                filled_quantity = trade.orderStatus.filled
                                average_price = trade.orderStatus.avgFillPrice
                                logger.info(f"Successfully closed long position: {filled_quantity} contracts at ${average_price}")
                                total_closed += filled_quantity
                                results.append({
                                    "action": "SELL",
                                    "symbol": pos.contract.symbol,
                                    "quantity": pos.position,
                                    "filled": filled_quantity,
                                    "price": average_price,
                                    "success": True
                                })
                            else:
                                logger.error(f"Failed to close long position: {trade.orderStatus.status}")
                                results.append({
                                    "action": "SELL",
                                    "symbol": pos.contract.symbol,
                                    "quantity": pos.position,
                                    "success": False,
                                    "error": trade.orderStatus.status
                                })
                        else:
                            logger.error(f"Order timeout for long position: {pos.contract.symbol}")
                            results.append({
                                "action": "SELL",
                                "symbol": pos.contract.symbol,
                                "quantity": pos.position,
                                "success": False,
                                "error": "Timeout"
                            })
                    except Exception as e:
                        logger.error(f"Error closing long position {pos.contract.symbol}: {e}")
                        results.append({
                            "action": "SELL",
                            "symbol": pos.contract.symbol,
                            "quantity": pos.position,
                            "success": False,
                            "error": str(e)
                        })
                        
                elif pos.position < 0:  # Short position - buy to close at market price
                    try:
                        logger.info(f"Closing short position: BUY {abs(pos.position)} {pos.contract.symbol} contracts at market price")
                        
                        # Ensure contract has exchange specified
                        contract = pos.contract
                        if not contract.exchange:
                            contract.exchange = 'CME'  # Default to CME for ES futures
                            logger.info(f"Set exchange to CME for contract: {contract.symbol}")
                        
                        # Use market order for immediate execution
                        order = MarketOrder('BUY', int(abs(pos.position)))
                        trade = self.ib.placeOrder(contract, order)
                    
                        # Wait for order to be filled
                        while not trade.isDone():
                            await asyncio.sleep(0.1)
                        
                        if trade.orderStatus.status == 'Filled':
                            filled_quantity = trade.orderStatus.filled
                            average_price = trade.orderStatus.avgFillPrice
                            logger.info(f"Successfully closed short position: {filled_quantity} contracts at ${average_price}")
                            total_closed += filled_quantity
                            results.append({
                                "action": "BUY_TO_CLOSE",
                                "symbol": pos.contract.symbol,
                                "quantity": abs(pos.position),
                                "filled": filled_quantity,
                                "price": average_price,
                                "success": True
                            })
                        else:
                            logger.error(f"Failed to close short position: {trade.orderStatus.status}")
                            results.append({
                                "action": "BUY_TO_CLOSE",
                                "symbol": pos.contract.symbol,
                                "quantity": abs(pos.position),
                                "success": False,
                                "error": trade.orderStatus.status
                            })
                    except Exception as e:
                        logger.error(f"Error closing short position {pos.contract.symbol}: {e}")
                        results.append({
                            "action": "BUY_TO_CLOSE",
                            "symbol": pos.contract.symbol,
                            "quantity": abs(pos.position),
                            "success": False,
                            "error": str(e)
                        })
            
            logger.info(f"Force close complete: {total_closed} contracts closed across {len(non_zero_positions)} positions")
            
            return {
                "message": f"Successfully closed {total_closed} contracts",
                "closed_positions": total_closed,
                "results": results
            }
            
        except Exception as e:
            error_msg = f"Error force closing positions: {e}"
            logger.error(error_msg)
            return {
                "message": error_msg,
                "closed_positions": 0,
                "results": []
            }

    async def close_all_positions(self) -> Dict[str, Any]:
        """Close all open positions"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IBKR")
            
            logger.info("Starting close_all_positions process...")
            positions = await self.get_positions()
            
            if not positions:
                logger.info("No positions found - sell alert skipped")
                return {
                    "message": "No positions to close",
                    "closed_positions": 0,
                    "results": []
                }
            
            logger.info(f"Found {len(positions)} positions to close")
            results = []
            total_closed = 0
            
            for i, position in enumerate(positions, 1):
                logger.info(f"Processing position {i}/{len(positions)}: {position.symbol} {position.quantity}")
                
                if position.quantity > 0:  # Long position
                    logger.info(f"Closing long position: SELL {position.quantity} contracts")
                    result = await self.sell_contracts(position.quantity)
                    results.append({
                        "action": "SELL",
                        "quantity": position.quantity,
                        "result": result.dict()
                    })
                    if result.success:
                        total_closed += result.filled_quantity
                        logger.info(f"Successfully closed long position: {result.filled_quantity} contracts")
                    else:
                        logger.error(f"Failed to close long position: {result.message}")
                        
                elif position.quantity < 0:  # Short position
                    logger.info(f"Closing short position: BUY {abs(position.quantity)} contracts")
                    result = await self.buy_contracts(abs(position.quantity))
                    results.append({
                        "action": "BUY_TO_CLOSE",
                        "quantity": abs(position.quantity),
                        "result": result.dict()
                    })
                    if result.success:
                        total_closed += result.filled_quantity
                        logger.info(f"Successfully closed short position: {result.filled_quantity} contracts")
                    else:
                        logger.error(f"Failed to close short position: {result.message}")
                else:
                    logger.info(f"Zero position skipped: {position.quantity}")
            
            logger.info(f"Close all positions complete: {total_closed} contracts closed across {len(positions)} positions")
            
            return {
                "message": f"Successfully closed {total_closed} contracts",
                "closed_positions": total_closed,
                "results": results
            }
            
        except Exception as e:
            error_msg = f"Error closing positions: {e}"
            logger.error(error_msg)
            return {
                "message": error_msg,
                "closed_positions": 0,
                "results": []
            }
