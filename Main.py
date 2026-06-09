mport asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8985680067:AAHROlAyLyMNf91fXw-IdtwQRJxcwda7OG8"

# ID каналов и пользователей
CHANNEL_USERNAME = "tgdesignstore"
REVIEWS_CHANNEL = "otzdesingstore"
MANAGER_USERNAME = "nelinner"
SHOP_CHANNEL = "tgdesingstore"

# Изображение только для главного меню
MENU_IMAGE = "https://ibb.co/RpCTX9X0"

SELLERS = {
    "seller_1": {
        "name": "LINNER",
        "contact": "@nelinner",      # Связь с продавцом
        "portfolio": "@worklinner",   # Портфолио
        "reviews": "@otzlinner",       # Отзывы продавца
    },
    "seller_2": {
        "name": "Loz",
        "contact": "@loz306",
        "portfolio": "@lozagin",
        "reviews": "@lozagin",
    },
    "seller_3": {
        "name": "cainfon",
        "contact": "@CAINFONN_17",
        "portfolio": "@seller3_portfolio",
        "reviews": "@cainfonreview",
    },
    "seller_4": {
        "name": "В поиске",
        "contact": "его тута нету",
        "portfolio": "работ больше чем у других",
        "reviews": "хз",
    },
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🛍️ Купить дизайн", callback_data="buy_design")
    )
    builder.row(
        InlineKeyboardButton(text="🤝 Отзывы магазина", callback_data="reviews"),
        InlineKeyboardButton(text="✊ Сотрудничество", callback_data="cooperation")
    )
    builder.row(
        InlineKeyboardButton(text="🌐 Канал магазина", callback_data="channel")
    )
    return builder.as_markup()

def sellers_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, seller in SELLERS.items():
        builder.row(InlineKeyboardButton(text=seller["name"], callback_data=key))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()

def back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()

async def show_main_menu(chat_id):
    try:
        caption = "🎨 Добро пожаловать в магазин дизайна!\nВыберите действие:"
        await bot.send_photo(
            chat_id=chat_id,
            photo=MENU_IMAGE,
            caption=caption,
            reply_markup=main_menu_keyboard()
        )
        logger.info(f"Главное меню отправлено в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки главного меню: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text="🎨 Добро пожаловать в магазин дизайна!\nВыберите действие:",
            reply_markup=main_menu_keyboard()
        )

@dp.message(Command("start"))
async def start_command(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    
    if not await check_subscription(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="[📲] Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton(text="[🔄] Проверить подписку", callback_data="check_sub")]
        ])
        await message.answer(
            "⚠️ Для использования бота необходимо подписаться на канал @tgdesignstore.",
            reply_markup=kb
        )
        return

    await show_main_menu(chat_id=message.chat.id)

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery):
    logger.info(f"Проверка подписки для пользователя {callback.from_user.id}")
    
    if not await check_subscription(callback.from_user.id):
        await callback.answer("❌ Вы ещё не подписались на канал!", show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")
    
    await show_main_menu(chat_id=callback.message.chat.id)
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    logger.info(f"Возврат в главное меню от пользователя {callback.from_user.id}")
    
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения при возврате: {e}")
    
    await show_main_menu(chat_id=callback.message.chat.id)
    await callback.answer()

@dp.callback_query(F.data == "buy_design")
async def buy_design(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} открыл раздел покупки дизайна")
    
    if not await check_subscription(callback.from_user.id):
        await callback.answer("⚠️ Сначала подпишитесь на канал!", show_alert=True)
        return
    
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")
    
    await callback.message.answer(
        "🛍️ Выберите себе подходящего дизайнера:",
        reply_markup=sellers_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.in_(SELLERS.keys()))
async def seller_info(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} выбрал продавца {callback.data}")
    
    if not await check_subscription(callback.from_user.id):
        await callback.answer("⚠️ Сначала подпишитесь на канал!", show_alert=True)
        return

    seller = SELLERS[callback.data]
    text = (
        f"📌 <b>Информация о дизайнере ^w^:</b>\n\n"
        f"1️⃣ Связь с продавцом: {seller['contact']}\n"
        f"2️⃣ Портфолио: {seller['portfolio']}\n"
        f"3️⃣ Отзывы продавца: {seller['reviews']}\n"
        f"4️⃣ Отзывы магазина: @{REVIEWS_CHANNEL}"
    )
    
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")
    
    await callback.message.answer(text, reply_markup=back_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "reviews")
async def reviews(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("⚠️ Сначала подпишитесь на канал!", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Открыть канал с отзывами", url=f"https://t.me/{REVIEWS_CHANNEL}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления: {e}")
    await callback.message.answer("🤝 Отзывы магазина:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "cooperation")
async def cooperation(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("⚠️ Сначала подпишитесь на канал!", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Связаться с руководителем", url=f"https://t.me/{MANAGER_USERNAME}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления: {e}")
    await callback.message.answer("✊ Сотрудничество:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "channel")
async def shop_channel(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("⚠️ Сначала подпишитесь на канал!", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Перейти в канал магазина", url=f"https://t.me/{SHOP_CHANNEL}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления: {e}")
    await callback.message.answer("🌐 Наш основной канал:", reply_markup=kb)
    await callback.answer()

async def main():
    logger.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
