import requests
import config
from telegram_bot import send_notification


class TronTracker:
    """Отслеживание TRC20 USDT транзакций на TRON."""
    
    def __init__(self):
        self.wallet = config.TRC20_WALLET
        self.usdt_contract = config.USDT_TRC20_CONTRACT
        self.min_amount = config.MIN_AMOUNT
        self.processed_txs = set()
        self.api_url = "https://api.trongrid.io"
    
    def get_trc20_transfers(self) -> list:
        """
        Получает TRC20 переводы на кошелек.
        
        Returns:
            Список транзакций
        """
        url = f"{self.api_url}/v1/accounts/{self.wallet}/transactions/trc20"
        params = {
            "only_to": "true",  # Только входящие
            "limit": 50,
            "contract_address": self.usdt_contract
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"[TRON] Ошибка API: {response.status_code}")
                return []
            
            data = response.json()
            return data.get("data", [])
            
        except Exception as e:
            print(f"[TRON] Ошибка запроса: {e}")
            return []
    
    def process_transactions(self, transactions: list) -> list:
        """
        Обрабатывает транзакции и возвращает новые.
        
        Args:
            transactions: Список транзакций от API
            
        Returns:
            Список новых транзакций для уведомления
        """
        new_transactions = []
        
        for tx in transactions:
            tx_id = tx.get("transaction_id")
            
            # Пропускаем уже обработанные
            if tx_id in self.processed_txs:
                continue
            
            # Проверяем что это входящая транзакция на наш кошелек
            to_address = tx.get("to")
            if to_address != self.wallet:
                continue
            
            # Получаем сумму (USDT имеет 6 decimals)
            value = tx.get("value", "0")
            decimals = int(tx.get("token_info", {}).get("decimals", 6))
            amount = int(value) / (10 ** decimals)
            
            # Фильтруем по минимальной сумме
            if amount < self.min_amount:
                self.processed_txs.add(tx_id)
                continue
            
            new_transactions.append({
                "tx_id": tx_id,
                "amount": amount,
                "token": "usdt",
                "network": "trc20"
            })
            
            self.processed_txs.add(tx_id)
        
        return new_transactions
    
    def check_and_notify(self) -> int:
        """
        Проверяет новые транзакции и отправляет уведомления.
        
        Returns:
            Количество новых уведомлений
        """
        transactions = self.get_trc20_transfers()
        new_txs = self.process_transactions(transactions)
        
        for tx in new_txs:
            print(f"[TRON] Новая транзакция: +{tx['amount']:.2f} USDT (TRC20)")
            send_notification(tx["amount"], "usdt")
        
        return len(new_txs)
    
    def load_processed(self, tx_ids: set):
        """Загружает ранее обработанные транзакции."""
        self.processed_txs = tx_ids
    
    def get_processed(self) -> set:
        """Возвращает множество обработанных транзакций."""
        return self.processed_txs


if __name__ == "__main__":
    # Тест
    tracker = TronTracker()
    print(f"Отслеживание кошелька: {tracker.wallet}")
    transactions = tracker.get_trc20_transfers()
    print(f"Найдено транзакций: {len(transactions)}")
    for tx in transactions[:5]:
        value = int(tx.get("value", 0)) / 1_000_000
        print(f"  - {value:.2f} USDT от {tx.get('from', 'unknown')[:10]}...")
