import requests
import config
from telegram_bot import send_notification


class BscTracker:
    """Отслеживание BEP20 USDT/BUSDT транзакций на BNB Chain."""
    
    def __init__(self):
        self.wallet = config.BEP20_WALLET.lower()
        self.usdt_contract = config.USDT_BEP20_CONTRACT.lower()
        self.busdt_contract = config.BUSDT_BEP20_CONTRACT.lower()
        self.min_amount = config.MIN_AMOUNT
        self.api_key = config.BSCSCAN_API_KEY
        self.processed_txs = set()
        self.api_url = "https://api.bscscan.com/api"
    
    def get_token_transfers(self, contract_address: str) -> list:
        """
        Получает BEP20 переводы на кошелек для указанного контракта.
        
        Args:
            contract_address: Адрес контракта токена
            
        Returns:
            Список транзакций
        """
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": contract_address,
            "address": self.wallet,
            "page": 1,
            "offset": 50,
            "sort": "desc"
        }
        
        if self.api_key:
            params["apikey"] = self.api_key
        
        try:
            response = requests.get(self.api_url, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"[BSC] Ошибка API: {response.status_code}")
                return []
            
            data = response.json()
            
            if data.get("status") != "1":
                # status "0" может означать просто отсутствие транзакций
                if data.get("message") != "No transactions found":
                    print(f"[BSC] API ответ: {data.get('message', 'Unknown error')}")
                return []
            
            return data.get("result", [])
            
        except Exception as e:
            print(f"[BSC] Ошибка запроса: {e}")
            return []
    
    def process_transactions(self, transactions: list, token_type: str) -> list:
        """
        Обрабатывает транзакции и возвращает новые входящие.
        
        Args:
            transactions: Список транзакций от API
            token_type: Тип токена ('usdt' или 'busdt')
            
        Returns:
            Список новых транзакций для уведомления
        """
        new_transactions = []
        
        for tx in transactions:
            tx_hash = tx.get("hash")
            
            # Пропускаем уже обработанные
            if tx_hash in self.processed_txs:
                continue
            
            # Проверяем что это входящая транзакция (to = наш кошелек)
            to_address = tx.get("to", "").lower()
            if to_address != self.wallet:
                self.processed_txs.add(tx_hash)
                continue
            
            # Получаем сумму (USDT/BUSDT имеют 18 decimals на BSC)
            value = tx.get("value", "0")
            decimals = int(tx.get("tokenDecimal", 18))
            amount = int(value) / (10 ** decimals)
            
            # Фильтруем по минимальной сумме
            if amount < self.min_amount:
                self.processed_txs.add(tx_hash)
                continue
            
            new_transactions.append({
                "tx_hash": tx_hash,
                "amount": amount,
                "token": token_type,
                "network": "bep20"
            })
            
            self.processed_txs.add(tx_hash)
        
        return new_transactions
    
    def check_and_notify(self) -> int:
        """
        Проверяет новые транзакции и отправляет уведомления.
        
        Returns:
            Количество новых уведомлений
        """
        total_notifications = 0
        
        # Проверяем USDT
        usdt_txs = self.get_token_transfers(self.usdt_contract)
        new_usdt = self.process_transactions(usdt_txs, "usdt")
        
        for tx in new_usdt:
            print(f"[BSC] Новая транзакция: +{tx['amount']:.2f} USDT (BEP20)")
            send_notification(tx["amount"], "usdt")
            total_notifications += 1
        
        # Проверяем BUSDT (BUSD)
        busdt_txs = self.get_token_transfers(self.busdt_contract)
        new_busdt = self.process_transactions(busdt_txs, "busdt")
        
        for tx in new_busdt:
            print(f"[BSC] Новая транзакция: +{tx['amount']:.2f} BUSDT (BEP20)")
            send_notification(tx["amount"], "busdt")
            total_notifications += 1
        
        return total_notifications
    
    def load_processed(self, tx_ids: set):
        """Загружает ранее обработанные транзакции."""
        self.processed_txs = tx_ids
    
    def get_processed(self) -> set:
        """Возвращает множество обработанных транзакций."""
        return self.processed_txs


if __name__ == "__main__":
    # Тест
    tracker = BscTracker()
    print(f"Отслеживание кошелька: {tracker.wallet}")
    
    print("\nПроверка USDT транзакций...")
    usdt_txs = tracker.get_token_transfers(tracker.usdt_contract)
    print(f"Найдено USDT транзакций: {len(usdt_txs)}")
    
    print("\nПроверка BUSDT транзакций...")
    busdt_txs = tracker.get_token_transfers(tracker.busdt_contract)
    print(f"Найдено BUSDT транзакций: {len(busdt_txs)}")
