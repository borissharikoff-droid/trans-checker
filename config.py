import os

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Wallet Addresses
TRC20_WALLET = os.getenv("TRC20_WALLET", "")
BEP20_WALLET = os.getenv("BEP20_WALLET", "")

# Contract Addresses (публичные, не секретные)
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
USDT_BEP20_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
BUSDT_BEP20_CONTRACT = "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"

# API Keys
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY", "")

# Settings
MIN_AMOUNT = int(os.getenv("MIN_AMOUNT", "5"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
STATE_FILE = "last_transactions.json"
