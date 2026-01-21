import requests
import config


def send_notification(amount: float, token_type: str) -> bool:
    """
    Отправляет уведомление о транзакции в Telegram.
    
    Args:
        amount: Сумма транзакции
        token_type: Тип токена ('usdt' или 'busdt')
    
    Returns:
        True если сообщение отправлено успешно
    """
    if not config.TELEGRAM_CHAT_ID:
        print("Ошибка: TELEGRAM_CHAT_ID не установлен в config.py")
        print("Запустите get_chat_id() и отправьте /start боту")
        return False
    
    message = f"+{amount:.2f} {token_type}"
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
        "message_thread_id": config.TELEGRAM_TOPIC_ID
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print(f"✅ Уведомление отправлено: {message}")
                return True
            else:
                print(f"❌ Ошибка Telegram API: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return False


def get_chat_id():
    """
    Запускает прослушивание обновлений для получения chat_id.
    Отправьте /start вашему боту в Telegram.
    """
    if not config.TELEGRAM_BOT_TOKEN:
        print("Ошибка: TELEGRAM_BOT_TOKEN не установлен!")
        print("Установите переменную окружения:")
        print('  export TELEGRAM_BOT_TOKEN="ваш_токен"')
        return
    
    print("Ожидание сообщения от вас в Telegram...")
    print(f"Отправьте /start вашему боту")
    print("Нажмите Ctrl+C для выхода\n")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
    last_update_id = 0
    
    while True:
        try:
            params = {"offset": last_update_id + 1, "timeout": 30}
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code != 200:
                print(f"Ошибка API: {response.text}")
                continue
            
            data = response.json()
            
            if not data.get("ok"):
                print(f"Ошибка: {data}")
                continue
            
            for update in data.get("result", []):
                last_update_id = update["update_id"]
                
                message = update.get("message", {})
                chat = message.get("chat", {})
                text = message.get("text", "")
                
                if chat:
                    chat_id = chat.get("id")
                    username = chat.get("username", "Unknown")
                    first_name = chat.get("first_name", "")
                    
                    print(f"\n{'='*50}")
                    print(f"Получено сообщение от: {first_name} (@{username})")
                    print(f"Текст: {text}")
                    print(f"\n>>> Ваш CHAT_ID: {chat_id} <<<")
                    print(f"\nДобавьте в Railway Variables:")
                    print(f"  TELEGRAM_CHAT_ID = {chat_id}")
                    print(f"{'='*50}\n")
                    
                    # Отправляем подтверждение
                    send_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
                    requests.post(send_url, json={
                        "chat_id": chat_id,
                        "text": f"✅ Ваш Chat ID: {chat_id}\n\nДобавьте его в config.py и перезапустите бота."
                    }, timeout=10)
                    
        except KeyboardInterrupt:
            print("\nВыход...")
            break
        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    # Запуск в режиме получения chat_id
    get_chat_id()
