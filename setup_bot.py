#!/usr/bin/env python3
"""
Complete setup script for ES Trading Bot
"""

import asyncio
import os
import sys
from contract_selector import ESContractSelector

def print_banner():
    """Print setup banner"""
    print("="*60)
    print("🚀 ES TRADING BOT SETUP")
    print("="*60)
    print()

def check_requirements():
    """Check if all requirements are installed"""
    print("📋 Checking requirements...")
    
    try:
        import fastapi
        import ib_insync
        import uvicorn
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

async def check_ibkr_connection():
    """Check if IBKR is running and accessible"""
    print("\n🔌 Checking IBKR connection...")
    
    try:
        from ib_insync import IB
        ib = IB()
        
        try:
            await ib.connectAsync('127.0.0.1', 7497, clientId=999)
            print("✅ IBKR connection successful")
            ib.disconnect()
            return True
        except Exception as e:
            print(f"❌ IBKR connection failed: {e}")
            print("Please ensure TWS or IB Gateway is running with API enabled")
            return False
            
    except Exception as e:
        print(f"❌ Error checking IBKR: {e}")
        return False

async def select_contracts():
    """Select ES contracts to trade"""
    print("\n📋 Selecting ES contracts...")
    
    selector = ESContractSelector()
    
    try:
        await selector.connect()
        contracts = await selector.find_es_contracts()
        
        if not contracts:
            print("❌ No ES contracts found")
            return False
        
        print(f"✅ Found {len(contracts)} ES contracts")
        
        # Display contracts
        selector.display_contracts()
        
        # Get user selection
        print("\nSelect contracts to trade:")
        print("Enter contract numbers separated by commas (e.g., 1,3,5)")
        print("Or enter 'all' to select all contracts")
        
        while True:
            try:
                selection = input("\nYour selection: ").strip().lower()
                
                if selection == 'all':
                    selected = contracts
                    break
                
                # Parse selection
                indices = [int(x.strip()) for x in selection.split(',')]
                selected = []
                
                for idx in indices:
                    if 1 <= idx <= len(contracts):
                        selected.append(contracts[idx-1])
                    else:
                        print(f"Invalid selection: {idx}")
                        break
                else:
                    break
                    
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")
            except KeyboardInterrupt:
                print("\nSetup cancelled.")
                return False
        
        if selected:
            print(f"\n✅ Selected {len(selected)} contract(s):")
            for i, contract in enumerate(selected, 1):
                print(f"  {i}. {contract.symbol} {contract.lastTradeDateOrContractMonth} ({contract.exchange})")
            
            # Save selection
            await save_contract_selection(selected)
            return True
        else:
            print("❌ No contracts selected")
            return False
    
    except Exception as e:
        print(f"❌ Error selecting contracts: {e}")
        return False
    finally:
        await selector.disconnect()

async def save_contract_selection(contracts):
    """Save selected contracts"""
    try:
        with open('selected_contracts.txt', 'w') as f:
            f.write("# Selected ES Contracts for Trading\n")
            f.write("# Format: symbol,month,exchange,currency,multiplier\n")
            for contract in contracts:
                multiplier = getattr(contract, 'multiplier', '50')
                f.write(f"{contract.symbol},{contract.lastTradeDateOrContractMonth},{contract.exchange},{contract.currency},{multiplier}\n")
        
        print("✅ Contract selection saved to 'selected_contracts.txt'")
        
        # Update config with primary contract
        if contracts:
            primary = contracts[0]
            print(f"📝 Primary contract: {primary.symbol} {primary.lastTradeDateOrContractMonth}")
    
    except Exception as e:
        print(f"❌ Error saving contracts: {e}")

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("\n📝 Creating .env file...")
        with open('.env', 'w') as f:
            f.write("# IBKR Configuration\n")
            f.write("IBKR_ACCOUNT_ID=your_account_id_here\n")
            f.write("IBKR_HOST=127.0.0.1\n")
            f.write("IBKR_PORT=7497\n")
            f.write("IBKR_CLIENT_ID=1\n")
            f.write("\n# Trading Configuration\n")
            f.write("CONTRACT_SYMBOL=ES\n")
            f.write("CONTRACT_MONTH=20250321\n")
            f.write("CONTRACT_EXCHANGE=CME\n")
            f.write("CONTRACT_CURRENCY=USD\n")
            f.write("\n# Logging Configuration\n")
            f.write("LOG_LEVEL=INFO\n")
            f.write("LOG_FILE=trading_bot.log\n")
        
        print("✅ .env file created")
        print("⚠️  Please edit .env file with your IBKR account details")
    else:
        print("✅ .env file already exists")

async def main():
    """Main setup function"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        return
    
    # Check IBKR connection
    if not await check_ibkr_connection():
        return
    
    # Create .env file
    create_env_file()
    
    # Select contracts
    if not await select_contracts():
        return
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Edit .env file with your IBKR account details")
    print("2. Start the trading bot: python run_bot.py")
    print("3. Test webhooks: python test_bot.py")
    print("\nWebhook URLs:")
    print("  Buy:  https://94d501344003.ngrok-free.app/ML-3-4/buy")
    print("  Sell: https://94d501344003.ngrok-free.app/ML-2-3-4/sell")
    print("\nStatus check: http://localhost:8000/status")

if __name__ == "__main__":
    asyncio.run(main())
