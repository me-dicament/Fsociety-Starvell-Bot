# 🐦 FSOCIETY MEDIC — Бот для Starvell

**FSOCIETY MEDIC** — Telegram-бот для автоматизации продавцов на бирже [Starvell](https://starvell.com).  
Основан на архитектуре FunPay Cardinal, адаптирован под Starvell с расширенным функционалом.

---

## 🤖 Возможности

### 📦 Автовыдача товаров
Привяжите товары к выдаваемым кодам/контенту — бот автоматически отправит покупателю при оплате.

### ⬆️ Автоподнятие лотов (бамп)
Автоматический подъём объявлений по расписанию. Настраиваемый интервал.

### 📩 Уведомления в Telegram
- ✅ Новые заказы
- 💬 Новые сообщения от покупателей
- 🔑 Авторизация на сайте
- ⬆️ Поднятие лотов
- ✅ Завершение заказов

### 💬 Ответы из Telegram
- Отвечайте на сообщения прямо из бота
- Быстрые шаблоны ответов
- Отправка фото

### 🔌 Система плагинов
Расширяйте функционал без правки кода бота.  
Плагины подгружаются из папки `plugins/`.

### 🛡️ Безопасность
- Вход по паролю (MD5)
- До 5 попыток, блокировка на 24ч
- Оповещения о попытках входа
- Раздельные переключатели уведомлений

### 🌐 Языки
Русский / English

---

## ⚡ Установка

### Windows
1. Скачайте и установите **Python 3.11+** (ставьте галочку "Add Python to PATH")
2. Скачайте [архив с ботом](https://github.com/me-dicament/Fsociety-Starvell-Bot/archive/refs/heads/main.zip)
3. Распакуйте в любую папку
4. Запустите `setup_bot.bat`
5. Запустите `start_bot.bat`
6. При первом запуске введите:
   - `BOT_TOKEN` — токен от [@BotFather](https://t.me/botfather)
   - Пароль для входа в бот
   - `SESSION_COOKIE` — сессия с Starvell (F12 → cookies)

### Linux (Ubuntu 22+)
```bash
wget -O setup_fsociety.sh https://raw.githubusercontent.com/me-dicament/Fsociety-Starvell-Bot/main/setup_starvell.sh
chmod +x setup_fsociety.sh
sudo ./setup_fsociety.sh
```

После установки запускайте бота:
```bash
python3 run_bot.py
```

---

## 🔧 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/restart` | Перезапуск бота |
| `/update` | Проверка обновлений |
| `/logs` | Архив логов |

---

## 🔌 Плагины

Управление через меню бота (`/start` → 🧩 Плагины).

### Свои плагины
Поместите `.py` файл в папку `plugins/`.  
Состояние плагинов сохраняется в `storage/plugins/state.json`.

### Канал с плагинами
Подписывайтесь на канал: *(скоро)*  
Чат сообщества: *(скоро)*

---

## 👨‍💻 Разработчик

- **Dev:** [@sellstarfast](https://t.me/sellstarfast)
- **Канал:** [@fsociety_starvell](https://t.me/fsociety_starvell)
- **Чат:** [@fsociety_starvell_chat](https://t.me/fsociety_starvell_chat)

---

## 📄 Лицензия

MIT License. Основано на [starvell_api](https://github.com/exfador/starvell_api) от @exfador.

---

## ⭐ Поддержка

Если бот полезен — поставьте звезду на GitHub! ✨
