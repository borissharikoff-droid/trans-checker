#!/usr/bin/env python3
"""
Crypto Wallet Tracker Bot
Отслеживает входящие USDT/BUSDT транзакции и отправляет уведомления в Telegram.
"""

import json
import time
import sys
from pathlib import Path

import config
from tron_tracker import TronTracker
from bsc_tracker import BscTracker


def load_state() -> dict:
    """Загружает состояние из файла."""
    state_file = Path(config.STATE_FILE)
    
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки состояния: {e}")
    
    return {"tron": [], "bsc": []}


def save_state(tron_txs: set, bsc_txs: set):
    """Сохраняет состояние в файл."""
    state = {
        "tron": list(tron_txs),
        "bsc": list(bsc_txs)
    }
    
    try:
        with open(config.STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения состояния: {e}")


def print_banner():
    """Выводит баннер при запуске."""
    print("=" * 60)
    print("       CRYPTO WALLET TRACKER BOT")
    print("=" * 60)
    print(f"\nОтслеживаемые кошельки:")
    print(f"  TRC20: {config.TRC20_WALLET}")
    print(f"  BEP20: {config.BEP20_WALLET}")
    print(f"\nМинимальная сумма для уведомления: {config.MIN_AMOUNT} USDT")
    print(f"Интервал проверки: {config.CHECK_INTERVAL} сек")
    print(f"BscScan API Key: {'установлен' if config.BSCSCAN_API_KEY else 'НЕТ'}")
    chat_id_display = config.TELEGRAM_CHAT_ID or "НЕ УСТАНОВЛЕН"
    print(f"\nChat ID: {chat_id_display}")
    
    print("\n" + "=" * 60)


def check_config():
    """Проверяет наличие критических настроек."""
    missing = []
    if not config.TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not config.TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if not config.TRC20_WALLET:
        missing.append("TRC20_WALLET")
    if not config.BEP20_WALLET:
        missing.append("BEP20_WALLET")
    
    if missing:
        print(f"\n❌ Не установлены переменные: {', '.join(missing)}")
        print("Добавьте их в Railway Variables")
        sys.exit(1)


def run_monitor():
    """Основной цикл мониторинга."""
    print_banner()
    check_config()
    
    # Инициализация трекеров
    tron_tracker = TronTracker()
    bsc_tracker = BscTracker()
    
    # Загрузка сохранённого состояния
    state = load_state()
    tron_tracker.load_processed(set(state.get("tron", [])))
    bsc_tracker.load_processed(set(state.get("bsc", [])))
    
    print(f"\nЗагружено из кэша:")
    print(f"  TRON транзакций: {len(tron_tracker.get_processed())}")
    print(f"  BSC транзакций: {len(bsc_tracker.get_processed())}")
    
    # Первый запуск - инициализируем без уведомлений
    print("\nИнициализация (первичная загрузка транзакций)...")
    
    # Загружаем текущие транзакции чтобы не спамить уведомлениями о старых
    tron_txs = tron_tracker.get_trc20_transfers()
    for tx in tron_txs:
        tron_tracker.processed_txs.add(tx.get("transaction_id"))
    
    bsc_usdt_txs = bsc_tracker.get_token_transfers(bsc_tracker.usdt_contract)
    bsc_busdt_txs = bsc_tracker.get_token_transfers(bsc_tracker.busdt_contract)
    for tx in bsc_usdt_txs + bsc_busdt_txs:
        bsc_tracker.processed_txs.add(tx.get("hash"))
    
    # Сохраняем начальное состояние
    save_state(tron_tracker.get_processed(), bsc_tracker.get_processed())
    
    print(f"Инициализировано транзакций:")
    print(f"  TRON: {len(tron_tracker.get_processed())}")
    print(f"  BSC: {len(bsc_tracker.get_processed())}")
    
    print(f"\n🚀 Мониторинг запущен! Нажмите Ctrl+C для остановки.\n")
    
    check_count = 0
    
    try:
        while True:
            check_count += 1
            
            # Проверяем TRON
            tron_notifications = tron_tracker.check_and_notify()
            
            # Небольшая пауза между API вызовами
            time.sleep(1)
            
            # Проверяем BSC
            bsc_notifications = bsc_tracker.check_and_notify()
            
            total = tron_notifications + bsc_notifications
            
            if total > 0:
                print(f"[{check_count}] Отправлено уведомлений: {total}")
                # Сохраняем состояние после новых транзакций
                save_state(tron_tracker.get_processed(), bsc_tracker.get_processed())
            else:
                # Периодически показываем что бот работает
                if check_count % 10 == 0:
                    print(f"[{check_count}] Проверка... новых транзакций нет")
            
            # Периодическое сохранение состояния
            if check_count % 20 == 0:
                save_state(tron_tracker.get_processed(), bsc_tracker.get_processed())
            
            time.sleep(config.CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nОстановка мониторинга...")
        save_state(tron_tracker.get_processed(), bsc_tracker.get_processed())
        print("Состояние сохранено. До свидания!")


if __name__ == "__main__":
    run_monitor()
