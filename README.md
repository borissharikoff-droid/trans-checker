# Crypto Wallet Tracker Bot

Telegram бот для отслеживания входящих USDT/BUSDT транзакций на кошельках TRC20 (TRON) и BEP20 (BNB Chain).

## Возможности

- Отслеживание USDT на TRC20 (TRON)
- Отслеживание USDT и BUSDT на BEP20 (BNB Chain)
- Уведомления в Telegram при поступлении более 5 USDT
- Формат уведомлений: `+{сумма} usdt` или `+{сумма} busdt`
- Сохранение состояния для избежания дубликатов после перезапуска

## Деплой на Railway

### 1. Создайте репозиторий на GitHub

```bash
cd "trans checker"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Подключите к Railway

1. Зайдите на [railway.app](https://railway.app)
2. Нажмите "New Project" → "Deploy from GitHub repo"
3. Выберите ваш репозиторий

### 3. Настройте переменные окружения (Variables)

В Railway Dashboard → Variables добавьте:

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | `123456:ABC...` |
| `TELEGRAM_CHAT_ID` | ID чата для уведомлений | `123456789` |
| `TRC20_WALLET` | Адрес TRC20 кошелька | `TW4i7h...` |
| `BEP20_WALLET` | Адрес BEP20 кошелька | `0x9dE6...` |
| `BSCSCAN_API_KEY` | (опционально) API ключ BscScan | `YOUR_KEY` |
| `MIN_AMOUNT` | (опционально) Мин. сумма, по умолчанию 5 | `5` |
| `CHECK_INTERVAL` | (опционально) Интервал проверки в сек | `30` |

### 4. Как получить TELEGRAM_CHAT_ID

Локально запустите:
```bash
TELEGRAM_BOT_TOKEN="ваш_токен" python telegram_bot.py
```
Отправьте `/start` боту в Telegram — он покажет ваш Chat ID.

## Локальный запуск

### Через переменные окружения

```bash
export TELEGRAM_BOT_TOKEN="ваш_токен"
export TELEGRAM_CHAT_ID="ваш_chat_id"
export TRC20_WALLET="ваш_trc20_адрес"
export BEP20_WALLET="ваш_bep20_адрес"

pip install -r requirements.txt
python main.py
```

### Через .env файл (опционально)

Создайте `.env` файл (он в .gitignore):
```
TELEGRAM_BOT_TOKEN=ваш_токен
TELEGRAM_CHAT_ID=ваш_chat_id
TRC20_WALLET=ваш_trc20_адрес
BEP20_WALLET=ваш_bep20_адрес
```

И используйте `python-dotenv` для загрузки.

## Структура файлов

```
├── config.py          # Конфигурация из env переменных
├── main.py            # Главный скрипт запуска
├── tron_tracker.py    # Отслеживание TRC20 транзакций
├── bsc_tracker.py     # Отслеживание BEP20 транзакций
├── telegram_bot.py    # Telegram уведомления
├── requirements.txt   # Зависимости
├── Procfile           # Конфиг для Railway
├── .gitignore         # Игнорируемые файлы
└── README.md          # Документация
```

## Примечания

- При первом запуске бот загружает текущие транзакции, чтобы не отправлять уведомления о старых переводах
- Состояние сохраняется в `last_transactions.json`
- Без BscScan API ключа действует лимит 1 запрос в 5 секунд
