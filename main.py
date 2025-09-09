import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List

from binance import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from dotenv import load_dotenv
from colorama import Fore, init
from tabulate import tabulate

load_dotenv()

# Initialize colorama
init(autoreset=True)

class TradingBotLogger:
    """Custom logger for trading bot operations"""
    def __init__(self, log_file: str = "trading_bot.log"):
        self.logger = logging.getLogger("TradingBot")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def info(self, message: str): self.logger.info(message)
    def error(self, message: str): self.logger.error(message)
    def warning(self, message: str): self.logger.warning(message)


class BasicBot:
    """Simplified Trading Bot for Binance Futures Testnet"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.logger = TradingBotLogger()
        self._symbol_info_cache: Dict[str, Any] = {}
        self.client = Client(api_key=api_key, api_secret=api_secret, testnet=testnet)
        self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
        self._test_connection()
        self.logger.info("Trading bot initialized successfully")
    
    def _test_connection(self):
        try:
            self.client.futures_ping()
            self.client.futures_account()
            self.logger.info("API connection successful")
        except Exception as e:
            self.logger.error(f"API connection failed: {e}")
            raise

    def get_account_balance(self) -> Dict[str, Any]:
        account = self.client.futures_account()
        balances = [b for b in account['assets'] if float(b['walletBalance']) > 0]
        return {
            'total_margin_balance': float(account['totalMarginBalance']),
            'available_balance': float(account['availableBalance']),
            'total_unrealized_pnl': float(account['totalUnrealizedProfit']),
            'balances': balances
        }

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        symbol_upper = symbol.upper()
        if symbol_upper in self._symbol_info_cache:
            return self._symbol_info_cache[symbol_upper]
        try:
            exchange_info = self.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol_upper:
                    info = {
                        'price_precision': s['pricePrecision'],
                        'quantity_precision': s['quantityPrecision'],
                        'min_qty': Decimal(next(f['minQty'] for f in s['filters'] if f['filterType'] == 'LOT_SIZE')),
                        'step_size': Decimal(next(f['stepSize'] for f in s['filters'] if f['filterType'] == 'LOT_SIZE')),
                    }
                    self._symbol_info_cache[symbol_upper] = info
                    return info
            raise ValueError(f"Symbol {symbol_upper} not found")
        except Exception as e:
            self.logger.error(f"Failed to get symbol info for {symbol_upper}: {e}")
            raise

    def get_current_price(self, symbol: str) -> float:
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol.upper())
            return float(ticker['price'])
        except Exception as e:
            self.logger.error(f"Failed to get price for {symbol}: {e}")
            raise

    def _validate_and_format_quantity(self, symbol: str, quantity: float) -> str:
        symbol_info = self.get_symbol_info(symbol)
        min_qty = symbol_info['min_qty']
        step_size = symbol_info['step_size']
        quantity_dec = Decimal(str(quantity))
        if quantity_dec < min_qty:
            raise ValueError(f"Quantity {quantity} is below minimum {min_qty}")
        adjusted_quantity = (quantity_dec // step_size) * step_size
        return f"{adjusted_quantity:.{symbol_info['quantity_precision']}f}"

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {'symbol': symbol.upper()} if symbol else {}
        orders = self.client.futures_get_open_orders(**params)
        return [self._format_order_response(o) for o in orders]

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        formatted_quantity = self._validate_and_format_quantity(symbol, quantity)
        order = self.client.futures_create_order(
            symbol=symbol.upper(), side=side.upper(), type='MARKET', quantity=formatted_quantity
        )
        return self._format_order_response(order)

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        formatted_quantity = self._validate_and_format_quantity(symbol, quantity)
        order = self.client.futures_create_order(
            symbol=symbol.upper(), side=side.upper(), type='LIMIT',
            timeInForce='GTC', quantity=formatted_quantity, price=f"{price}"
        )
        return self._format_order_response(order)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        return self.client.futures_cancel_order(symbol=symbol.upper(), orderId=order_id)

    def _format_order_response(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Formats the raw order from Binance into a consistent dictionary."""
        return {
            'order_id': order['orderId'],
            'symbol': order['symbol'],
            'side': order['side'],
            'type': order['type'],
            'quantity': float(order['origQty']),
            'price': float(order.get('price', 0)),
            'status': order['status'],
        }

class TradingBotCLI:
    """Command Line Interface for the Trading Bot"""
    
    def __init__(self):
        self.bot: Optional[BasicBot] = None
        self.running = True
    
    def print_header(self):
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}    BINANCE FUTURES TRADING BOT - TESTNET")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}[!] TESTNET ONLY - NO REAL MONEY INVOLVED")
        print(f"{Fore.GREEN}[+] API Setup: https://testnet.binancefuture.com/")
        print(f"{Fore.CYAN}{'='*60}\n")
    
    def get_api_credentials(self) -> tuple[str, str]:
        api_key = os.getenv('BINANCE_TESTNET_API_KEY')
        api_secret = os.getenv('BINANCE_TESTNET_API_SECRET')
        if api_key and api_secret:
            print(f"{Fore.GREEN}[+] Found credentials in .env file.")
            return api_key, api_secret
        print(f"{Fore.YELLOW}[!] Credentials not found in .env file. Please enter them manually.")
        api_key = input(f"{Fore.CYAN}Enter your API Key: ").strip()
        api_secret = input(f"{Fore.CYAN}Enter your API Secret: ").strip()
        return api_key, api_secret
    
    def initialize_bot(self):
        try:
            api_key, api_secret = self.get_api_credentials()
            if not api_key or not api_secret:
                print(f"{Fore.RED}[X] API Key and Secret are required.")
                return False
            print(f"\n{Fore.YELLOW}Initializing bot...")
            self.bot = BasicBot(api_key, api_secret, testnet=True)
            print(f"{Fore.GREEN}[+] Bot initialized successfully!")
            self.show_account_balance()
            return True
        except Exception as e:
            print(f"{Fore.RED}[X] Failed to initialize bot: {e}")
            return False
    
    def show_account_balance(self):
        try:
            balance = self.bot.get_account_balance()
            print(f"\n{Fore.CYAN}--- ACCOUNT BALANCE ---")
            pnl_color = Fore.GREEN if balance['total_unrealized_pnl'] >= 0 else Fore.RED
            print(f"{Fore.WHITE}Total Margin Balance: {Fore.GREEN}${balance['total_margin_balance']:.2f}")
            print(f"{Fore.WHITE}Available Balance:    {Fore.GREEN}${balance['available_balance']:.2f}")
            print(f"{Fore.WHITE}Unrealized PnL:       {pnl_color}${balance['total_unrealized_pnl']:.2f}")
            if balance['balances']:
                headers = ['Asset', 'Wallet Balance']
                rows = [[b['asset'], f"${float(b['walletBalance']):.2f}"] for b in balance['balances']]
                print(tabulate(rows, headers=headers, tablefmt="grid"))
        except Exception as e:
            print(f"{Fore.RED}[X] Failed to get balance: {e}")

    def show_current_price(self):
        symbol = input(f"{Fore.CYAN}Enter symbol (e.g., BTCUSDT): ").strip().upper()
        if not symbol: return
        try:
            price = self.bot.get_current_price(symbol)
            print(f"{Fore.GREEN}Current price of {symbol}: ${price:,.2f}")
        except Exception as e:
            print(f"{Fore.RED}[X] Failed to get price for {symbol}: {e}")

    def place_order_cli(self, order_type: str):
        try:
            symbol = input(f"{Fore.CYAN}Enter symbol (e.g., BTCUSDT): ").strip().upper()
            side = input(f"{Fore.CYAN}Enter side (BUY/SELL): ").strip().upper()
            quantity = float(input(f"{Fore.CYAN}Enter quantity: ").strip())
            
            if side not in ['BUY', 'SELL'] or quantity <= 0:
                raise ValueError("Invalid side or quantity.")

            if order_type == 'LIMIT':
                price = float(input(f"{Fore.CYAN}Enter limit price: ").strip())
                result = self.bot.place_limit_order(symbol, side, quantity, price)
            else: # MARKET
                result = self.bot.place_market_order(symbol, side, quantity)
            
            print(f"\n{Fore.GREEN}[+] {order_type} order placed successfully!")
            self._display_order_result(result)
        except Exception as e:
            print(f"{Fore.RED}[X] Failed to place order: {e}")

    def show_open_orders(self):
        try:
            orders = self.bot.get_open_orders()
            if not orders:
                print(f"{Fore.BLUE}No open orders found.")
                return
            headers = ['ID', 'Symbol', 'Side', 'Type', 'Qty', 'Price', 'Status']
            rows = [
                [o['order_id'], o['symbol'], o['side'], o['type'], 
                 o['quantity'], f"${o['price']:.2f}", o['status']] for o in orders
            ]
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        except Exception as e:
            print(f"{Fore.RED}[X] Failed to get open orders: {e}")
            
    def cancel_order_cli(self):
        try:
            self.show_open_orders()
            orders = self.bot.get_open_orders()
            if not orders: return
            
            order_id = int(input(f"\n{Fore.CYAN}Enter Order ID to cancel: ").strip())
            target_order = next((o for o in orders if o['order_id'] == order_id), None)
            
            if not target_order:
                print(f"{Fore.RED}[X] Order ID not found.")
                return

            result = self.bot.cancel_order(target_order['symbol'], order_id)
            print(f"\n{Fore.GREEN}[+] Order {order_id} cancelled successfully.")
        except Exception as e:
            print(f"{Fore.RED}[X] Failed to cancel order: {e}")

    def _display_order_result(self, result: Dict[str, Any]):
        print(f"{Fore.CYAN}{'-'*20}")
        for key, value in result.items():
            print(f"{Fore.WHITE}{key.replace('_', ' ').title()}: {Fore.GREEN}{value}")
        print(f"{Fore.CYAN}{'-'*20}")
    
    def show_menu(self):
        menu = {
            "1": "View Account Balance", "2": "Check Current Price",
            "3": "Place Market Order",   "4": "Place Limit Order",
            "5": "View Open Orders",     "6": "Cancel Order",
            "7": "Exit"
        }
        print(f"\n{Fore.CYAN}{'='*20}\n[MENU]\n{'-'*20}")
        for key, value in menu.items():
            print(f"{Fore.WHITE}{key}. {value}")
        print(f"{'='*20}")
    
    def run(self):
        self.print_header()
        if not self.initialize_bot(): return
        
        actions = {
            '1': self.show_account_balance, '2': self.show_current_price,
            '3': lambda: self.place_order_cli('MARKET'), '4': lambda: self.place_order_cli('LIMIT'),
            '5': self.show_open_orders, '6': self.cancel_order_cli,
        }
        
        while self.running:
            self.show_menu()
            choice = input(f"{Fore.CYAN}Enter your choice: ").strip()
            if choice == '7':
                self.running = False
                print(f"{Fore.GREEN}Goodbye!")
                continue
            
            action = actions.get(choice)
            if action: action()
            else: print(f"{Fore.RED}[X] Invalid choice.")
            
            if self.running: input(f"\n{Fore.YELLOW}Press Enter to continue...")

def main():
    """Main entry point"""
    try:
        cli = TradingBotCLI()
        cli.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Application interrupted by user.")
    except Exception as e:
        print(f"{Fore.RED}[X] Fatal error: {e}")
    finally:
        print(f"{Fore.CYAN}Application terminated.")

if __name__ == "__main__":
    main()

