import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Токен вашего бота
BOT_TOKEN = "8985680067:AAHROlAyLyMNf91fXw-IdtwQRJxcwda7OG8"

# ID каналов и пользователей (username без @)
CHANNEL_USERNAME = "tgdesignstore"          # канал, на который нужна обязательная подписка
REVIEWS_CHANNEL = "otzdesingstore"       # канал с отзывами магазина
MANAGER_USERNAME = "nelinner"            # руководитель для сотрудничества
SHOP_CHANNEL = "tgdesignstore"             # основной канал магазина

# Данные продавцов (замените на реальные username)
SELLERS = {
    "seller_1": {
        "name": "linner",
        "contact": "@nelinner",
        "reviews": "@otzlinner",
    },
    "seller_2": {
        "name": "cainfon",
        "contact": "@CAINFONN_17",
        "reviews": "@cainfonreview",
    },
    "seller_3": {
        "name": "loz",
        "contact": "@loz306",
        "reviews": "@lozagin",
    },
    "seller_4": {
        "name": "Soon 💤",
        "contact": "soon",
        "reviews": "soon",
    },
}

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Проверка подписки на канал
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

# Клавиатура главного меню
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

# Клавиатура выбора продавца
def sellers_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, seller in SELLERS.items():
        builder.row(InlineKeyboardButton(text=seller["name"], callback_data=key))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()

# Клавиатура с кнопкой "Назад" для информационных сообщений
def back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()

# Стартовое сообщение
@dp.message(Command("start"))
async def start_command(message: types.Message):
    if not await check_subscription(message.from_user.id):
        # Пользователь не подписан – предлагаем подписаться
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_sub")]
        ])
        await message.answer(
            "Для использования бота необходимо подписаться на канал @tgdesignstore.",
            reply_markup=kb
        )
        return

    # Подписан – показываем главное меню
    await message.answer(
        "Добро пожаловать в магазин дизайна!",
        reply_markup=main_menu_keyboard()
    )

# Проверка подписки по кнопке "Проверить подписку"
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("Вы ещё не подписались на канал!", show_alert=True)
        return

    # Подписка оформлена – удаляем старое сообщение и показываем меню
    await callback.message.delete()
    await callback.message.answer(
        "Спасибо за подписку! Теперь вы можете пользоваться ботом.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

# Обработчик возврата в главное меню
@dp.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

# 🛍️ Купить дизайн – показать продавцов
@dp.callback_query(F.data == "buy_design")
async def buy_design(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("Сначала подпишитесь на канал!", show_alert=True)
        return
    await callback.message.delete()
    await callback.message.answer(
        "🪪 Выберите продавца:",
        reply_markup=sellers_keyboard()
    )
    await callback.answer()

# Обработчик выбора конкретного продавца
@dp.callback_query(F.data.in_(SELLERS.keys()))
async def seller_info(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("Сначала подпишитесь на канал!", show_alert=True)
        return

    seller = SELLERS[callback.data]
    text = (
        f"📌 Информация о продавце:\n\n"
        f"1️⃣ Связь с продавцом: {seller['contact']}\n"
        f"2️⃣ Отзывы продавца: {seller['reviews']}\n"
        f"3️⃣ Отзывы магазина: @{REVIEWS_CHANNEL}\n"
    )
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=back_keyboard())
    await callback.answer()

# 🤝 Отзывы магазина
@dp.callback_query(F.data == "reviews")
async def reviews(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("Сначала подпишитесь на канал!", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Открыть канал с отзывами", url=f"https://t.me/{REVIEWS_CHANNEL}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await callback.message.delete()
    await callback.message.answer(
        "Отзывы магазина:",
        reply_markup=kb
    )
    await callback.answer()

# ✊ Сотрудничество
@dp.callback_query(F.data == "cooperation")
async def cooperation(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("Сначала подпишитесь на канал!", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Связаться с руководителем", url=f"https://t.me/{MANAGER_USERNAME}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await callback.message.delete()
    await callback.message.answer(
        "Сотрудничество:",
        reply_markup=kb
    )
    await callback.answer()

# 🌐 Канал магазина
@dp.callback_query(F.data == "channel")
async def shop_channel(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("Сначала подпишитесь на канал!", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Перейти в канал магазина", url=f"https://t.me/{SHOP_CHANNEL}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await callback.message.delete()
    await callback.message.answer(
        "Наш основной канал:",
        reply_markup=kb
    )
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
