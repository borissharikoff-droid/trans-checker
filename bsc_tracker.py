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
            "offset": 100,  # Увеличиваем лимит для лучшего покрытия
            "sort": "desc"
        }
        
        if self.api_key:
            params["apikey"] = self.api_key
        
        try:
            response = requests.get(self.api_url, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"[BSC] ❌ Ошибка API: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            
            if data.get("status") != "1":
                # status "0" может означать просто отсутствие транзакций
                msg = data.get("message", "")
                result = data.get("result", "")
                if msg != "No transactions found":
                    print(f"[BSC] ⚠️ API: {msg} - {result}")
                return []
            
            result = data.get("result", [])
            if isinstance(result, list):
                return result
            return []
            
        except Exception as e:
            print(f"[BSC] ❌ Ошибка запроса: {e}")
            import traceback
            traceback.print_exc()
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
            if not tx_hash:
                continue
            
            # Пропускаем уже обработанные
            if tx_hash in self.processed_txs:
                # Логируем только для входящих транзакций, чтобы не спамить
                to_address_check = tx.get("to", "").lower()
                if to_address_check == self.wallet:
                    value_check = tx.get("value", "0")
                    decimals_check = int(tx.get("tokenDecimal", 18))
                    amount_check = int(value_check) / (10 ** decimals_check)
                    if amount_check >= self.min_amount:
                        print(f"[BSC] ⚠️ Транзакция {tx_hash[:16]}... уже обработана (сумма: {amount_check:.6f})")
                continue
            
            # Проверяем что это входящая транзакция (to = наш кошелек)
            to_address = tx.get("to", "").lower()
            from_address = tx.get("from", "").lower()
            
            # Логируем для отладки
            if to_address == self.wallet:
                # Получаем сумму (USDT/BUSDT имеют 18 decimals на BSC)
                value = tx.get("value", "0")
                decimals = int(tx.get("tokenDecimal", 18))
                amount = int(value) / (10 ** decimals)
                
                print(f"[BSC] Найдена входящая транзакция {token_type.upper()}: {tx_hash[:10]}... сумма: {amount:.6f}, мин: {self.min_amount}")
                
                # Фильтруем по минимальной сумме
                if amount < self.min_amount:
                    print(f"[BSC] Транзакция {tx_hash[:10]}... пропущена: сумма {amount:.6f} < {self.min_amount}")
                    self.processed_txs.add(tx_hash)
                    continue
                
                new_transactions.append({
                    "tx_hash": tx_hash,
                    "amount": amount,
                    "token": token_type,
                    "network": "bep20"
                })
                
                self.processed_txs.add(tx_hash)
            else:
                # Это исходящая транзакция или транзакция на другой адрес
                # Помечаем как обработанную, чтобы не проверять снова
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
        print(f"[BSC] Получено USDT транзакций от API: {len(usdt_txs)}")
        new_usdt = self.process_transactions(usdt_txs, "usdt")
        
        for tx in new_usdt:
            print(f"[BSC] ✅ Новая транзакция: +{tx['amount']:.2f} USDT (BEP20) | Hash: {tx['tx_hash'][:16]}...")
            if send_notification(tx["amount"], "USDT BNB"):
                total_notifications += 1
            else:
                print(f"[BSC] ❌ Ошибка отправки уведомления для транзакции {tx['tx_hash'][:16]}...")
        
        # Проверяем BUSDT (BUSD)
        busdt_txs = self.get_token_transfers(self.busdt_contract)
        print(f"[BSC] Получено BUSDT транзакций от API: {len(busdt_txs)}")
        new_busdt = self.process_transactions(busdt_txs, "busdt")
        
        for tx in new_busdt:
            print(f"[BSC] ✅ Новая транзакция: +{tx['amount']:.2f} BUSDT (BEP20) | Hash: {tx['tx_hash'][:16]}...")
            if send_notification(tx["amount"], "BUSD BNB"):
                total_notifications += 1
            else:
                print(f"[BSC] ❌ Ошибка отправки уведомления для транзакции {tx['tx_hash'][:16]}...")
        
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
