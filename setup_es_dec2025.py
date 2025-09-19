#!/usr/bin/env python3
"""
Setup script specifically for ES DEC 2025 CME futures
"""

import asyncio
import os
from contract_selector import ESContractSelector

def print_banner():
    """Print setup banner"""
    print("="*60)
    print("🚀 ES DEC 2025 CME FUTURES TRADING BOT SETUP")
    print("="*60)
    print()

def create_env_file():
    """Create .env file for ES DEC 2025"""
    print("📝 Creating .env file for ES DEC 2025...")
    
    with open('.env', 'w') as f:
        f.write("# IBKR Configuration\n")
        f.write("IBKR_ACCOUNT_ID=your_account_id_here\n")
        f.write("IBKR_HOST=127.0.0.1\n")
        f.write("IBKR_PORT=7497\n")
        f.write("IBKR_CLIENT_ID=1\n")
        f.write("\n# Trading Configuration - ES DEC 2025\n")
        f.write("CONTRACT_SYMBOL=ES\n")
        f.write("CONTRACT_MONTH=20251219\n")
        f.write("CONTRACT_EXCHANGE=CME\n")
        f.write("CONTRACT_CURRENCY=USD\n")
        f.write("\n# Logging Configuration\n")
        f.write("LOG_LEVEL=INFO\n")
        f.write("LOG_FILE=trading_bot.log\n")
    
    print("✅ .env file created for ES DEC 2025")

def create_contracts_file():
    """Create contracts file for ES DEC 2025"""
    print("📝 Creating contracts file for ES DEC 2025...")
    
    with open('selected_contracts.txt', 'w') as f:
        f.write("# Selected ES Contracts for Trading\n")
        f.write("# Format: symbol,month,exchange,currency,multiplier\n")
        f.write("# ES DEC 2025 CME Future\n")
        f.write("ES,20251219,CME,USD,50\n")
    
    print("✅ Contracts file created for ES DEC 2025")

async def verify_contract():
    """Verify ES DEC 2025 contract is available"""
    print("\n🔍 Verifying ES DEC 2025 contract availability...")
    
    selector = ESContractSelector()
    
    try:
        await selector.connect()
        contracts = await selector.find_es_contracts()
        
        if not contracts:
            print("❌ No ES contracts found")
            return False
        
        # Look for DEC 2025 specifically
        dec2025_contracts = [c for c in contracts if '20251219' in c.lastTradeDateOrContractMonth]
        
        if dec2025_contracts:
            print("✅ ES DEC 2025 contract found!")
            for contract in dec2025_contracts:
                print(f"   - {contract.symbol} {contract.lastTradeDateOrContractMonth} ({contract.exchange})")
            return True
        else:
            print("⚠️  ES DEC 2025 contract not found, but other ES contracts are available:")
            for i, contract in enumerate(contracts[:5], 1):  # Show first 5
                print(f"   {i}. {contract.symbol} {contract.lastTradeDateOrContractMonth} ({contract.exchange})")
            
            print("\nWould you like to:")
            print("1. Use a different ES contract")
            print("2. Continue with ES DEC 2025 (may not be available yet)")
            
            choice = input("\nYour choice (1 or 2): ").strip()
            
            if choice == "1":
                return await select_alternative_contract(contracts)
            else:
                print("✅ Continuing with ES DEC 2025 configuration")
                return True
    
    except Exception as e:
        print(f"❌ Error verifying contract: {e}")
        print("✅ Continuing with ES DEC 2025 configuration")
        return True
    finally:
        await selector.disconnect()

async def select_alternative_contract(contracts):
    """Select an alternative ES contract"""
    print("\n📋 Available ES contracts:")
    for i, contract in enumerate(contracts, 1):
        print(f"   {i}. {contract.symbol} {contract.lastTradeDateOrContractMonth} ({contract.exchange})")
    
    while True:
        try:
            choice = input(f"\nSelect contract (1-{len(contracts)}): ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(contracts):
                selected = contracts[idx]
                print(f"✅ Selected: {selected.symbol} {selected.lastTradeDateOrContractMonth}")
                
                # Update contracts file
                with open('selected_contracts.txt', 'w') as f:
                    f.write("# Selected ES Contracts for Trading\n")
                    f.write("# Format: symbol,month,exchange,currency,multiplier\n")
                    f.write(f"{selected.symbol},{selected.lastTradeDateOrContractMonth},{selected.exchange},{selected.currency},50\n")
                
                # Update .env file
                with open('.env', 'r') as f:
                    content = f.read()
                
                content = content.replace('CONTRACT_MONTH=20251219', f'CONTRACT_MONTH={selected.lastTradeDateOrContractMonth}')
                
                with open('.env', 'w') as f:
                    f.write(content)
                
                print("✅ Configuration updated with selected contract")
                return True
            else:
                print(f"Invalid choice. Please select 1-{len(contracts)}")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nSelection cancelled.")
            return False

async def main():
    """Main setup function"""
    print_banner()
    
    print("This setup will configure the bot for ES DEC 2025 CME futures trading.")
    print()
    
    # Create configuration files
    create_env_file()
    create_contracts_file()
    
    # Verify contract availability
    if not await verify_contract():
        print("❌ Setup cancelled")
        return
    
    print("\n" + "="*60)
    print("🎉 ES DEC 2025 SETUP COMPLETE!")
    print("="*60)
    print("\nConfiguration:")
    print("  Contract: ES DEC 2025 (20251219)")
    print("  Exchange: CME")
    print("  Currency: USD")
    print("  Multiplier: 50")
    print("\nNext steps:")
    print("1. Edit .env file with your IBKR account details")
    print("2. Start IBKR TWS or IB Gateway with API enabled")
    print("3. Start the trading bot: python run_bot.py")
    print("\nWebhook URLs:")
    print("  Buy:  https://94d501344003.ngrok-free.app/ML-3-4/buy")
    print("  Sell: https://94d501344003.ngrok-free.app/ML-2-3-4/sell")
    print("\nStatus check: http://localhost:8000/status")

if __name__ == "__main__":
    asyncio.run(main())
