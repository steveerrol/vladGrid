#!/usr/bin/env python3
"""
Quick setup script - no IBKR connection required
"""

import os

def print_banner():
    """Print setup banner"""
    print("="*60)
    print("🚀 ES TRADING BOT QUICK SETUP")
    print("="*60)
    print()

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("📝 Creating .env file...")
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
    else:
        print("✅ .env file already exists")

def create_sample_contracts():
    """Create sample contracts file"""
    if not os.path.exists('selected_contracts.txt'):
        print("📝 Creating sample contracts file...")
        with open('selected_contracts.txt', 'w') as f:
            f.write("# Selected ES Contracts for Trading\n")
            f.write("# Format: symbol,month,exchange,currency,multiplier\n")
            f.write("# ES,20250321,CME,USD,50\n")
            f.write("# ES,20250620,CME,USD,50\n")
        
        print("✅ Sample contracts file created")
    else:
        print("✅ Contracts file already exists")

def main():
    """Main setup function"""
    print_banner()
    
    print("This quick setup will:")
    print("1. Create .env configuration file")
    print("2. Create sample contracts file")
    print("3. Show you how to run the bot")
    print()
    
    # Create .env file
    create_env_file()
    
    # Create sample contracts
    create_sample_contracts()
    
    print("\n" + "="*60)
    print("🎉 QUICK SETUP COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Edit .env file with your IBKR account details")
    print("2. Start IBKR TWS or IB Gateway with API enabled")
    print("3. Run contract selector: python select_contracts.py")
    print("4. Start the trading bot: python run_bot.py")
    print("\nWebhook URLs:")
    print("  Buy:  https://94d501344003.ngrok-free.app/ML-3-4/buy")
    print("  Sell: https://94d501344003.ngrok-free.app/ML-2-3-4/sell")
    print("\nStatus check: http://localhost:8000/status")

if __name__ == "__main__":
    main()
