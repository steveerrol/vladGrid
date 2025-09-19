#!/usr/bin/env python3
"""
ES Contract Selector - Find and select available ES contracts
"""

import asyncio
import logging
from ib_insync import IB, Contract
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ESContractSelector:
    """Find and select available ES contracts"""
    
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.available_contracts = []
    
    async def connect(self):
        """Connect to IBKR"""
        try:
            await self.ib.connectAsync(
                Config.IBKR_HOST, 
                Config.IBKR_PORT, 
                clientId=Config.IBKR_CLIENT_ID
            )
            self.connected = True
            logger.info(f"Connected to IBKR at {Config.IBKR_HOST}:{Config.IBKR_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    async def find_es_contracts(self):
        """Find all available ES contracts"""
        try:
            if not self.connected:
                raise Exception("Not connected to IBKR")
            
            logger.info("Searching for available ES contracts...")
            
            # Search for ES futures contracts
            search_contract = Contract(
                secType='FUT',
                symbol='ES',
                exchange='CME',
                currency='USD'
            )
            
            # Get all available ES contracts
            contracts = await self.ib.qualifyContractsAsync(search_contract)
            
            if not contracts:
                logger.warning("No ES contracts found")
                return []
            
            # Filter and sort contracts by expiration date
            es_contracts = []
            for contract in contracts:
                if (contract.symbol == 'ES' and 
                    contract.secType == 'FUT' and 
                    contract.exchange == 'CME'):
                    es_contracts.append(contract)
            
            # Sort by lastTradeDateOrContractMonth
            es_contracts.sort(key=lambda x: x.lastTradeDateOrContractMonth)
            
            self.available_contracts = es_contracts
            return es_contracts
            
        except Exception as e:
            logger.error(f"Error finding ES contracts: {e}")
            return []
    
    def display_contracts(self):
        """Display available contracts in a formatted table"""
        if not self.available_contracts:
            print("No ES contracts available")
            return
        
        print("\n" + "="*80)
        print("AVAILABLE ES CONTRACTS")
        print("="*80)
        print(f"{'#':<3} {'Symbol':<8} {'Month':<12} {'Exchange':<8} {'Currency':<8} {'Multiplier':<10}")
        print("-"*80)
        
        for i, contract in enumerate(self.available_contracts, 1):
            month = contract.lastTradeDateOrContractMonth
            multiplier = getattr(contract, 'multiplier', '50')
            print(f"{i:<3} {contract.symbol:<8} {month:<12} {contract.exchange:<8} {contract.currency:<8} {multiplier:<10}")
        
        print("="*80)
    
    def select_contracts(self):
        """Interactive contract selection"""
        if not self.available_contracts:
            print("No contracts available for selection")
            return []
        
        self.display_contracts()
        
        print("\nSelect ES contract(s) to trade:")
        print("Enter contract numbers separated by commas (e.g., 1,3,5)")
        print("Or enter 'all' to select all contracts")
        print("Or enter 'q' to quit")
        
        while True:
            try:
                selection = input("\nYour selection: ").strip().lower()
                
                if selection == 'q':
                    return []
                
                if selection == 'all':
                    return self.available_contracts
                
                # Parse comma-separated numbers
                indices = [int(x.strip()) for x in selection.split(',')]
                
                # Validate indices
                selected_contracts = []
                for idx in indices:
                    if 1 <= idx <= len(self.available_contracts):
                        selected_contracts.append(self.available_contracts[idx-1])
                    else:
                        print(f"Invalid selection: {idx}. Please choose between 1-{len(self.available_contracts)}")
                        break
                else:
                    return selected_contracts
                    
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")
            except KeyboardInterrupt:
                print("\nSelection cancelled.")
                return []

async def main():
    """Main function to find and select ES contracts"""
    selector = ESContractSelector()
    
    try:
        print("🔍 ES Contract Selector")
        print("="*50)
        
        # Connect to IBKR
        print("Connecting to IBKR...")
        await selector.connect()
        
        # Find available contracts
        print("Finding available ES contracts...")
        contracts = await selector.find_es_contracts()
        
        if not contracts:
            print("❌ No ES contracts found")
            return
        
        print(f"✅ Found {len(contracts)} ES contracts")
        
        # Display and select contracts
        selected = selector.select_contracts()
        
        if selected:
            print(f"\n✅ Selected {len(selected)} contract(s):")
            for i, contract in enumerate(selected, 1):
                print(f"  {i}. {contract.symbol} {contract.lastTradeDateOrContractMonth} ({contract.exchange})")
            
            # Save selection to config
            print("\n💾 Saving selection to config...")
            await save_contract_selection(selected)
        else:
            print("❌ No contracts selected")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
    
    finally:
        await selector.disconnect()

async def save_contract_selection(contracts):
    """Save selected contracts to a config file"""
    try:
        # Create a contracts config file
        with open('selected_contracts.txt', 'w') as f:
            f.write("# Selected ES Contracts for Trading\n")
            f.write("# Format: symbol,month,exchange,currency,multiplier\n")
            for contract in contracts:
                multiplier = getattr(contract, 'multiplier', '50')
                f.write(f"{contract.symbol},{contract.lastTradeDateOrContractMonth},{contract.exchange},{contract.currency},{multiplier}\n")
        
        print("✅ Contract selection saved to 'selected_contracts.txt'")
        
        # Also update the main config
        if contracts:
            primary_contract = contracts[0]
            print(f"📝 Primary contract set to: {primary_contract.symbol} {primary_contract.lastTradeDateOrContractMonth}")
            
            # Update config.py
            update_config_file(primary_contract)
    
    except Exception as e:
        logger.error(f"Error saving contract selection: {e}")

def update_config_file(contract):
    """Update config.py with the selected contract"""
    try:
        # Read current config
        with open('config.py', 'r') as f:
            content = f.read()
        
        # Update contract month
        old_line = f"CONTRACT_MONTH = os.getenv('CONTRACT_MONTH', '{Config.CONTRACT_MONTH}')"
        new_line = f"CONTRACT_MONTH = os.getenv('CONTRACT_MONTH', '{contract.lastTradeDateOrContractMonth}')"
        
        content = content.replace(old_line, new_line)
        
        # Write updated config
        with open('config.py', 'w') as f:
            f.write(content)
        
        print("✅ Config file updated with selected contract")
    
    except Exception as e:
        logger.error(f"Error updating config: {e}")

if __name__ == "__main__":
    asyncio.run(main())
