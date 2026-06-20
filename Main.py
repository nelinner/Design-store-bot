import asyncio
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import BadRequest
import aiohttp
from bs4 import BeautifulSoup

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8985680067:AAHROlAyLyMNf91fXw-IdtwQRJxcwda7OG8"
CHANNEL_USERNAME = "@tgdesignstore"
CHANNEL_ID = "@tgdesignstore"

# Все ссылки на изображения – можно использовать обычные ссылки ibb.co (страницы), бот сам достанет прямые ссылки
MAIN_MENU_IMAGE = "https://ibb.co/RpCTX9X0"          # Главное меню
BUY_DESIGN_IMAGE = "https://ibb.co/C5MTqxQ9"         # Раздел «Купить дизайн»

# ===== ДАННЫЕ ПРОДАВЦОВ =====
SELLERS = {
    "linner": {
        "name": "Linner",
        "description": "💎 Профессиональный дизайнер каналов и логотипов",
        "image_url": "https://ibb.co/8LXw3Fw8",
        "fields": {
            "Username": "@nelinner",
            "Портфолио": "@worklinner",
            "Отзывы": "@otzlinner",
            "Прайс": "https://t.me/pricedesignstore/2",
        },
    },
    "loz": {
        "name": "Loz",
        "description": "🎨 Креативный дизайн и уникальный стиль",
        "image_url": "https://ibb.co/Xk5NGtd0",
        "fields": {
            "Username": "@loz306",
            "Портфолио": "@lozportfolio",
            "Отзывы": "Вручение от руководителя",
            "Прайс": "Узнавать в лс",
        },
    },
    "r1polz": {
        "name": "r1polZ",
        "description": "🚀 Оформление со стилем",
        "image_url": "https://ibb.co/8J6HGnk",
        "fields": {
            "Username": "@m9Zzzzuta",
            "Портфолио": "узнавать в лс",
            "Отзывы": "вручение от руководителя",
            "Прайс": "узнавать в лс",
        },
    },
    "rassvet": {
        "name": "Рассвет",
        "description": "🌅 Стильные решения для твоего проекта",
        "image_url": "https://ibb.co/Tqc8D19p",   # ← твоя новая ссылка
        "fields": {
            "Username": "@PACBETTT",         # ← замени на реальный контакт
            "Портфолио": "https://t.me/rasvetDesignn",
            "Отзывы": "вручение от руководителя",
            "Прайс": "https://t.me/pricedesignstore/3",
        },
    },
    "omut": {
        "name": "Омут сомнений // asc ",
        "description": "🌀 Минимализм и атмосферный дизайн, и оформление каналов",
        "image_url": "https://ibb.co/4nVRrgp9",
        "fields": {
            "Username": "@xaywd",
            "Портфолио": "https://t.me/movaningfx",
            "Отзывы": "вручение от руководителя",
            "Прайс": "https://t.me/pricedesignstore/4",
        },
    },
}

# ===== ТЕКСТЫ =====
RULES_TEXT = (
    "📃 <b>Регламент магазина</b>\n\n"
    "1. Перед покупкой обязательно ознакомьтесь с портфолио и отзывами продавца.\n"
    "2. Все сделки проводятся только через официальных продавцов, указанных в боте.\n"
    "3. Запрещено передавать контакты продавцов третьим лицам без согласования.\n"
    "4. Магазин не несёт ответственности за качество работ, если вы обратились к исполнителю "
    "напрямую, минуя этот бот.\n"
    "5. Любые споры решаются через руководителя @nelinner.\n"
    "6. Сохраняйте все чеки и переписки до завершения сделки.\n\n"
    "Нарушение регламента может привести к блокировке доступа к боту."
)

SUPPORT_TEXT = (
    "📞 <b>Поддержка бота</b>\n\n"
    "Если у вас возникли вопросы, проблемы с ботом или нужна консультация — "
    "напишите руководителю: <b>@nelinner</b>\n\n"
    "Пожалуйста, опишите вашу проблему максимально подробно, приложите скриншоты при необходимости."
)

# ===== КЭШ ДЛЯ ПРЯМЫХ ССЫЛОК =====
url_cache = {}

async def get_direct_image_url(ibb_url: str) -> Optional[str]:
    """
    Превращает ссылку на страницу ibb.co (или уже прямую) в прямую ссылку на изображение.
    Результат кэшируется в памяти.
    """
    # Если ссылка уже прямая (содержит i.ibb.co) – возвращаем как есть
    if "i.ibb.co" in ibb_url:
        return ibb_url

    if ibb_url in url_cache:
        return url_cache[ibb_url]

    # Если это не ibb.co – возвращаем без изменений
    if "ibb.co" not in ibb_url:
        return ibb_url

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ibb_url, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"Не удалось загрузить страницу {ibb_url}")
                    return None
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')

        # Ищем прямую ссылку в meta og:image
        meta_og = soup.find('meta', property='og:image')
        if meta_og and meta_og.get('content'):
            direct_url = meta_og['content']
            url_cache[ibb_url] = direct_url
            return direct_url

        # Альтернатива: ищем link[rel="image_src"]
        link_rel = soup.find('link', rel='image_src')
        if link_rel and link_rel.get('href'):
            direct_url = link_rel['href']
            url_cache[ibb_url] = direct_url
            return direct_url

        # Если ничего не нашли
        logger.warning(f"Не найдена прямая ссылка на странице {ibb_url}")
        return None

    except Exception as e:
        logger.error(f"Ошибка при парсинге {ibb_url}: {e}")
        return None

# ===== КЛАВИАТУРЫ =====
def build_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛍️ Купить дизайн", callback_data="buy_design")],
        [
            InlineKeyboardButton("⭐ Отзывы магазина", url="https://t.me/otzdesingstore"),
            InlineKeyboardButton("🌐 Канал магазина", url="https://t.me/tgdesignstore"),
        ],
        [
            InlineKeyboardButton("📃 Регламент магазина", callback_data="rules"),
            InlineKeyboardButton("📞 Поддержка бота", callback_data="support"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def build_sellers_keyboard():
    buttons = []
    for key, seller in SELLERS.items():
        buttons.append([InlineKeyboardButton(seller["name"], callback_data=f"seller_{key}")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(buttons)

def build_seller_detail_keyboard(seller_key: str):
    seller = SELLERS[seller_key]
    keyboard = []
    for field_name, value in seller["fields"].items():
        if value.startswith("http://") or value.startswith("https://") or value.startswith("@"):
            url = f"https://t.me/{value[1:]}" if value.startswith("@") else value
            keyboard.append([InlineKeyboardButton(field_name, url=url)])
        else:
            callback_data = f"field_{seller_key}_{field_name}"
            keyboard.append([InlineKeyboardButton(field_name, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_sellers")])
    return InlineKeyboardMarkup(keyboard)

# ===== ПРОВЕРКА ПОДПИСКИ =====
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except BadRequest as e:
        logger.warning(f"Ошибка проверки подписки: {e}")
        return False

async def require_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    user_id = query.from_user.id if query else update.message.from_user.id
    if await is_subscribed(user_id, context):
        return True

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")]]
    )
    text = (
        "🔒 Для использования бота необходимо быть подписанным на канал "
        f"{CHANNEL_USERNAME}.\nПодпишись и нажми кнопку ниже."
    )
    if query:
        try:
            await query.message.delete()
        except BadRequest:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat_id, text=text, reply_markup=keyboard
        )
    else:
        await update.message.reply_text(text, reply_markup=keyboard)
    return False

# ===== ОБРАБОТЧИКИ КОМАНД =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start – БЕЗ удаления сообщения пользователя."""
    # Сообщение /start теперь остаётся в чате
    if not await is_subscribed(update.message.from_user.id, context):
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")]]
        )
        await update.message.reply_text(
            f"🔒 Для использования бота подпишитесь на канал {CHANNEL_USERNAME} и нажмите кнопку.",
            reply_markup=keyboard,
        )
        return

    await show_main_menu(update, context, chat_id=update.message.chat_id)

async def show_main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int
) -> None:
    # Получаем прямую ссылку для главного меню
    direct_url = await get_direct_image_url(MAIN_MENU_IMAGE)
    if direct_url:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=direct_url,
                caption="🏠 <b>Главное меню</b>",
                parse_mode="HTML",
                reply_markup=build_main_menu_keyboard(),
            )
            return
        except BadRequest as e:
            logger.error(f"Ошибка при отправке главного меню: {e}")

    # Если не удалось – текстовый вариант
    await context.bot.send_message(
        chat_id=chat_id,
        text="🏠 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=build_main_menu_keyboard(),
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    # Проверка подписки для всех действий, кроме check_sub и field_
    if data != "check_sub" and not data.startswith("field_"):
        if not await require_subscription(update, context):
            return

    # Удаляем предыдущее сообщение бота (не для всплывающих подсказок)
    if not data.startswith("field_"):
        try:
            await query.message.delete()
        except BadRequest:
            pass

    if data == "check_sub":
        if await is_subscribed(user_id, context):
            try:
                await query.message.delete()
            except BadRequest:
                pass
            await show_main_menu(update, context, chat_id=query.message.chat_id)
        else:
            await query.answer("❌ Вы всё ещё не подписаны на канал!", show_alert=True)

    elif data == "buy_design":
        direct_url = await get_direct_image_url(BUY_DESIGN_IMAGE)
        if direct_url:
            try:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=direct_url,
                    caption="🛍️ <b>Выберите продавца дизайна:</b>",
                    parse_mode="HTML",
                    reply_markup=build_sellers_keyboard(),
                )
                return
            except BadRequest:
                pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🛍️ <b>Выберите продавца дизайна:</b>",
            parse_mode="HTML",
            reply_markup=build_sellers_keyboard(),
        )

    elif data.startswith("seller_"):
        seller_key = data[len("seller_"):]
        if seller_key in SELLERS:
            seller = SELLERS[seller_key]
            direct_url = await get_direct_image_url(seller["image_url"])

            # Формируем подпись: имя + описание (если есть)
            caption = f"👤 <b>{seller['name']}</b>"
            if seller.get("description"):
                caption += f"\n{seller['description']}"

            if direct_url:
                try:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=direct_url,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=build_seller_detail_keyboard(seller_key),
                    )
                    return
                except BadRequest:
                    pass
            # Запасной текстовый вариант
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=caption,
                parse_mode="HTML",
                reply_markup=build_seller_detail_keyboard(seller_key),
            )

    elif data.startswith("field_"):
        _, seller_key, field_name = data.split("_", 2)
        seller = SELLERS.get(seller_key)
        if seller:
            text = seller["fields"].get(field_name, "Информация отсутствует")
            await query.answer(text, show_alert=True)

    elif data == "back_to_main":
        await show_main_menu(update, context, chat_id=query.message.chat_id)

    elif data == "back_to_sellers":
        direct_url = await get_direct_image_url(BUY_DESIGN_IMAGE)
        if direct_url:
            try:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=direct_url,
                    caption="🛍️ <b>Выберите продавца дизайна:</b>",
                    parse_mode="HTML",
                    reply_markup=build_sellers_keyboard(),
                )
                return
            except BadRequest:
                pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🛍️ <b>Выберите продавца дизайна:</b>",
            parse_mode="HTML",
            reply_markup=build_sellers_keyboard(),
        )

    elif data == "rules":
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]]
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=RULES_TEXT,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    elif data == "support":
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]]
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=SUPPORT_TEXT,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    else:
        await query.answer("Неизвестная команда", show_alert=True)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_error_handler(error_handler)
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
