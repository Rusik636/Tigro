# 🐯 Tigro — Microservice Framework for Telegram Bots

**Tigro** — это микро-библиотека для построения масштабируемых Telegram-ботов в
микросервисной архитектуре с использованием **FastStream**, **RabbitMQ** и **FastAPI**.
Tigro предоставляет высокоуровневый DSL для написания хендлеров (`@command`, `@callback`, `@message`) прямо внутри микросервисов, не привязывая Telegram API к конкретному сервису.

---

## 🚀 Быстрый старт

1. **Установите зависимости:**
   - Python 3.10+
   - RabbitMQ
   - FastStream, aiogram, fastapi, pydantic

2. **Структура проекта:**
   ```
   project/
     gBot/           # Gateway-бот (aiogram)
     tService/       # Микросервис (ваша бизнес-логика)
     lib/tigro/      # Tigro (локальная библиотека)
     shared/         # (опционально) общие схемы
   ```

3. **Пример микросервиса:**
   ```python
   from tigro import ModuleRouter, Context, cb_btn, inline_kb

   router = ModuleRouter()

   @router.command("/start")
   async def start(ctx: Context):
       await ctx.send_message(
           "Привет! Это Tigro 👋\nВыберите действие:",
           markup=inline_kb(
               cb_btn("ℹ️ Помощь", "help"),
               cb_btn("⚙️ Настройки", "settings"),
               row_width=2
           ),
           parse_mode="HTML"
       )

   @router.callback("help")
   async def help_handler(ctx: Context):
       await ctx.edit_message(
           "<b>Помощь</b>\n\nЗдесь вы найдёте ответы на вопросы.",
           markup=inline_kb(cb_btn("Назад", "back")),
           parse_mode="HTML"
       )
   ```

4. **Пример gateway-бота (gBot/main.py):**
   ```python
   from tigro.gateway import run_gateway
   TOKEN = "<your-telegram-token>"
   BROKER_URL = "amqp://guest:guest@localhost/"
   if __name__ == "__main__":
       run_gateway(TOKEN, BROKER_URL)
   ```

---

## 🏗️ Архитектура

- **gBot** (gateway):
  - Получает Telegram update через aiogram
  - Преобразует в TgEvent и отправляет в RabbitMQ
  - Получает TgResponse и отправляет ответ пользователю
- **Микросервисы**:
  - Получают TgEvent из очереди
  - Обрабатывают через Tigro Router/Context
  - Формируют ответы через ctx.send_message / ctx.edit_message
  - Отправляют TgResponse обратно в gateway

---

## 🧩 Основные компоненты

- **Router** — маршрутизатор событий (command, callback, message)
- **Context** — формирует ответы, не знает о транспорте
- **ModuleRouter** — группировка хендлеров по модулям
- **cb_btn, inline_kb, inline_kb_grid** — декларативное создание клавиатур
- **SOLID** — все компоненты легко расширяются без изменения кода

---

## ✨ Примеры использования

### Команды и колбэки
```python
@router.command("/start")
async def start(ctx: Context):
    await ctx.send_message("Привет!", markup=inline_kb(cb_btn("Помощь", "help")))

@router.callback("help")
async def help(ctx: Context):
    await ctx.edit_message("Это раздел помощи", parse_mode="Markdown")
```

### Клавиатуры
```python
keyboard = inline_kb(
    cb_btn("Кнопка 1", "cb1"),
    cb_btn("Кнопка 2", "cb2"),
    row_width=2
)
```

### Форматирование текста
```python
await ctx.send_message("<b>Жирный</b> и <i>курсив</i>", parse_mode="HTML")
await ctx.edit_message("*Жирный* и _курсив_", parse_mode="Markdown")
```

---

## 🛠️ Расширяемость и SOLID
- Добавляйте новые типы команд через наследование MessageCommand
- Добавляйте новые типы клавиатур через отдельные функции
- Все публичные API максимально узкие и расширяемые
- Контекст не зависит от транспорта, только от абстракций

---

## ⚡ Поддержка parse_mode
- Любой вызов `send_message` или `edit_message` поддерживает `parse_mode` (`"HTML"`, `"Markdown"`)
- Можно расширить команды для поддержки других параметров (disable_web_page_preview и т.д.)

---

## 🔌 Выбор Telegram-фреймворка для gateway

Tigro поддерживает разные Telegram-фреймворки для gateway-бота. По умолчанию используется aiogram, но вы можете реализовать и подключить свой класс (например, для Telebot).

**Пример:**
```python
from tigro.gateway import run_gateway
run_gateway(TOKEN, BROKER_URL, framework="aiogram")  # или framework="telebot"
```

Чтобы добавить поддержку нового фреймворка:
- Реализуйте класс, наследующийся от BaseGateway (см. tigro/gateway/base.py)
- Зарегистрируйте его в GATEWAY_REGISTRY в tigro/gateway/__init__.py

---

## ❓ FAQ

**Q: Как добавить новую команду/кнопку?**
A: Просто добавьте новый хендлер с нужным декоратором и используйте cb_btn/inline_kb.

**Q: Как добавить свой transport?**
A: Реализуйте свой ResponsePublisher и передайте его в Router.

**Q: Как добавить новые параметры в сообщения?**
A: Расширьте MessageCommand или добавьте новые классы-команды.

**Q: Как добавить middleware?**
A: Передайте список middlewares в Router.

---

## 🧑‍💻 Контакты и поддержка
- Telegram: @your_support
- Email: support@example.com

---

## Лицензия
MIT

---

## Изменения в 0.1.1

- Удалён метод `Context.flush`, ответы отправляются автоматически после завершения хендлера.

## 🔧 Особенности

- ✅ Поддержка `@command`, `@message`, `@callback` — в стиле `aiogram`
- ✅ Абстракция `ctx.send_message(...)`, `ctx.edit_message(...)` для формирования ответов
- ✅ Полностью **асинхронная** архитектура
- ✅ Разделение ответственности: парсинг update — в `gateway_bot`, бизнес-логика — в микросервисах
- ✅ Работа через **RabbitMQ + FastStream** (можно заменить)
- ✅ Поддержка middleware, расширяемость, соответствие принципам **SOLID**

---
