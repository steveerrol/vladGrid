#!/usr/bin/env python3
"""
Restart the bot to load new code
"""

import subprocess
import time
import requests
import sys

def restart_bot():
    """Restart the bot"""
    print("🔄 Restarting Bot to Load New Code")
    print("="*50)
    
    try:
        # Check if bot is running
        print("1. Checking if bot is running...")
        try:
            response = requests.get("http://localhost:8000/status", timeout=5)
            if response.status_code == 200:
                print("✅ Bot is currently running")
            else:
                print("❌ Bot is not responding properly")
        except:
            print("❌ Bot is not running")
        
        print("\n2. Please restart the bot manually:")
        print("   • Stop the current bot (Ctrl+C)")
        print("   • Run: python run_bot.py")
        print("   • Or run: python main.py")
        
        print("\n3. After restarting, test the sell alert:")
        print("   • Run: python test_sell_fix.py")
        
        print("\n💡 The new code should now:")
        print("   • Use market orders instead of limit orders")
        print("   • Close positions immediately at market price")
        print("   • Not require bid/ask price data")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    restart_bot()
