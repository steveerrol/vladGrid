from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import asyncio
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
from trading_bot import TradingBot
from models import AlertRequest
from config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="ES DEC 2025 CME Trading Bot", version="1.0.0")

# Initialize trading bot
trading_bot = None

@app.on_event("startup")
async def startup_event():
    """Initialize the trading bot on startup"""
    global trading_bot
    try:
        trading_bot = TradingBot()
        await trading_bot.connect()
        logger.info("Trading bot initialized and connected to IBKR")
    except Exception as e:
        logger.error(f"Failed to initialize trading bot: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global trading_bot
    if trading_bot:
        await trading_bot.disconnect()
        logger.info("Trading bot disconnected")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "ES DEC 2025 CME Trading Bot is running", "status": "healthy"}

@app.get("/status")
async def get_status():
    """Get trading bot status"""
    if not trading_bot:
        return {"status": "not_initialized"}

    # Get contract information
    contracts_info = []
    if trading_bot.contracts:
        for contract in trading_bot.contracts:
            contracts_info.append({
                "symbol": contract.symbol,
                "month": contract.lastTradeDateOrContractMonth,
                "exchange": contract.exchange,
                "currency": contract.currency
            })

    return {
        "status": "connected" if trading_bot.is_connected() else "disconnected",
        "contracts": contracts_info,
        "primary_contract": contracts_info[0] if contracts_info else None,
        "positions": await trading_bot.get_positions(),
        "account_info": await trading_bot.get_account_info()
    }

@app.get("/bid-ask")
async def get_bid_ask():
    """Get current bid/ask prices"""
    try:
        if not trading_bot:
            raise HTTPException(status_code=500, detail="Trading bot not initialized")
        
        if not trading_bot.is_connected():
            raise HTTPException(status_code=500, detail="Not connected to IBKR")
        
        # Get primary contract
        contract = trading_bot.get_primary_contract()
        if not contract:
            raise HTTPException(status_code=500, detail="No contract available")
        
        # Get market data
        market_data = await trading_bot.get_market_data(contract)
        
        if not market_data:
            raise HTTPException(status_code=500, detail="Could not get market data")
        
        # Calculate spread
        spread = None
        if market_data['ask'] and market_data['bid']:
            spread = market_data['ask'] - market_data['bid']
        
        return {
            "symbol": contract.symbol,
            "month": contract.lastTradeDateOrContractMonth,
            "bid": market_data['bid'],
            "ask": market_data['ask'],
            "last": market_data['last'],
            "spread": spread,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting bid/ask: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ML-2-3-4/sell")
async def sell_alert(request: Request):
    """Handle sell alert from TradingView - close all positions"""
    try:
        logger.info("="*50)
        logger.info("SELL ALERT RECEIVED FROM TRADINGVIEW")
        logger.info("="*50)
        
        if not trading_bot:
            logger.error("Trading bot not initialized")
            raise HTTPException(status_code=500, detail="Trading bot not initialized")
        
        if not trading_bot.is_connected():
            logger.error("Not connected to IBKR")
            raise HTTPException(status_code=500, detail="Not connected to IBKR")
        
        logger.info("Trading bot is connected and ready")
        
        # Get current positions
        logger.info("Checking current positions...")
        positions = await trading_bot.get_positions()
        
        if not positions:
            logger.info("No positions found - sell alert skipped as expected")
            return {
                "message": "No positions to close",
                "status": "skipped",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"Found {len(positions)} positions to close:")
        for i, pos in enumerate(positions, 1):
            logger.info(f"  {i}. {pos.symbol}: {pos.quantity} @ ${pos.average_price}")
        
        # Close all positions at market price (immediate execution)
        logger.info("Starting position closure process at market prices...")
        try:
            # Close all positions with market orders
            results = []
            total_closed = 0
            
            for position in positions:
                if position.quantity > 0:  # Long position - sell at market price
                    result = await trading_bot.sell_contracts(position.quantity)
                    results.append({
                        "action": "SELL_AT_MARKET",
                        "quantity": position.quantity,
                        "result": result.dict()
                    })
                    if result.success:
                        total_closed += result.filled_quantity
                elif position.quantity < 0:  # Short position - buy to close at market price
                    result = await trading_bot.buy_contracts(abs(position.quantity))
                    results.append({
                        "action": "BUY_TO_CLOSE_AT_MARKET",
                        "quantity": abs(position.quantity),
                        "result": result.dict()
                    })
                    if result.success:
                        total_closed += result.filled_quantity
            
            result = {
                "message": f"Successfully closed {total_closed} contracts at market prices",
                "closed_positions": total_closed,
                "results": results
            }
                
        except Exception as e:
            logger.error(f"Error in market close: {e}")
            # Fallback to force close
            logger.info("Falling back to force close...")
            result = await trading_bot.close_all_positions_force()
        
        logger.info(f"Sell alert processing complete: {result}")
        logger.info("="*50)
        
        return {
            "message": "Sell alert processed successfully",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing sell alert: {e}")
        logger.error("="*50)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ML-3-4/buy")
async def buy_alert(request: Request):
    """Handle buy alert from TradingView - buy 3 contracts"""
    try:
        logger.info("Received BUY alert from TradingView")
        
        if not trading_bot:
            raise HTTPException(status_code=500, detail="Trading bot not initialized")
        
        if not trading_bot.is_connected():
            raise HTTPException(status_code=500, detail="Not connected to IBKR")
        
        # Buy 3 contracts at market price (immediate execution)
        result = await trading_bot.buy_contracts(3)
        
        logger.info(f"Successfully processed buy alert: {result}")
        
        return {
            "message": "Buy alert processed successfully",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing buy alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ML-3-4/buy-limit")
async def buy_limit_alert(request: Request):
    """Handle buy limit alert from TradingView - buy 3 contracts at ask price"""
    try:
        logger.info("Received BUY LIMIT alert from TradingView")
        
        if not trading_bot:
            raise HTTPException(status_code=500, detail="Trading bot not initialized")
        
        if not trading_bot.is_connected():
            raise HTTPException(status_code=500, detail="Not connected to IBKR")
        
        # Get price from request body if provided
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        price = body.get("price")
        
        # Buy 3 contracts at ask price (or specified price)
        result = await trading_bot.buy_contracts_limit(3, price)
        
        logger.info(f"Successfully processed buy limit alert: {result}")
        
        return {
            "message": "Buy limit alert processed successfully",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing buy limit alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ML-2-3-4/sell-limit")
async def sell_limit_alert(request: Request):
    """Handle sell limit alert from TradingView - sell all positions at bid price"""
    try:
        logger.info("Received SELL LIMIT alert from TradingView")
        
        if not trading_bot:
            raise HTTPException(status_code=500, detail="Trading bot not initialized")
        
        if not trading_bot.is_connected():
            raise HTTPException(status_code=500, detail="Not connected to IBKR")
        
        # Get price from request body if provided
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        price = body.get("price")
        
        # Get current positions
        positions = await trading_bot.get_positions()
        
        if not positions:
            logger.info("No positions found - sell limit alert skipped")
            return {
                "message": "No positions to close",
                "status": "skipped",
                "timestamp": datetime.now().isoformat()
            }
        
        # Close all positions with limit orders
        results = []
        total_closed = 0
        
        for position in positions:
            if position.quantity > 0:  # Long position
                result = await trading_bot.sell_contracts_limit(position.quantity, price)
                results.append({
                    "action": "SELL_LIMIT",
                    "quantity": position.quantity,
                    "result": result.dict()
                })
                if result.success:
                    total_closed += result.filled_quantity
            elif position.quantity < 0:  # Short position
                result = await trading_bot.buy_contracts_limit(abs(position.quantity), price)
                results.append({
                    "action": "BUY_TO_CLOSE_LIMIT",
                    "quantity": abs(position.quantity),
                    "result": result.dict()
                })
                if result.success:
                    total_closed += result.filled_quantity
        
        logger.info(f"Sell limit alert processing complete: {total_closed} contracts closed")
        
        return {
            "message": f"Sell limit alert processed successfully - closed {total_closed} contracts",
            "closed_positions": total_closed,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing sell limit alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
