import os
import asyncio
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatMemberUpdated
)

TOKEN = os.getenv("9105049033:AAGd6nkK-owMIBCFBVG7C2F_bbneigDfpOE")
ADMIN_ID = 7723079442

CHANNELS = [
    "@smsonayturkiyem",
    "@swarovskiyeniden",
    "@swarovskihile"
]

OWNER = "https://t.me/SwarovskiOwner"

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def init_db():
    async with aiosqlite.connect("swarovski.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                interactions INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            INSERT INTO stats (interactions)
            SELECT 0 WHERE NOT EXISTS (
                SELECT 1 FROM stats
            )
        """)
        await db.commit()


async def add_user(user_id):
    async with aiosqlite.connect("swarovski.db") as db:
        await db.execute(
            "INSERT OR IGNORE INTO users VALUES (?)",
            (user_id,)
        )
        await db.commit()


async def interaction():
    async with aiosqlite.connect("swarovski.db") as db:
        await db.execute(
            "UPDATE stats SET interactions = interactions + 1"
        )
        await db.commit()


async def is_member(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(
                channel, user_id
            )
            if member.status not in (
                "member", "administrator", "creator"
            ):
                return False
        except Exception:
            return False
    return True


def join_keyboard():
    buttons = [
        [InlineKeyboardButton(
            text=f"📢 {channel}",
            url=f"https://t.me/{channel[1:]}"
        )]
        for channel in CHANNELS
    ]

    buttons.append([
        InlineKeyboardButton(
            text="✅ Katıldım, kontrol et",
            callback_data="check"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🟢 Ucuz No",
            url=OWNER
        )],
        [InlineKeyboardButton(
            text="💎 Kaliteli No",
            url=OWNER
        )],
        [InlineKeyboardButton(
            text="👨‍💻 Admin ile iletişime geç",
            url=OWNER
        )]
    ])


async def show_menu(message):
    await message.answer(
        "👑 SWAROVSKI 👑\n\n"
        "Hoş geldin!\n"
        "İstediğin uygulama için numara al.\n\n"
        "📱 Bir paket seç:",
        reply_markup=main_keyboard()
    )


@dp.message(CommandStart())
async def start(message: Message):
    await add_user(message.from_user.id)
    await interaction()

    if not await is_member(message.from_user.id):
        await message.answer(
            "👑 SWAROVSKI 👑\n\n"
            "Botu kullanabilmek için üç kanalımıza "
            "da katılmalısın!",
            reply_markup=join_keyboard()
        )
        return

    await show_menu(message)


@dp.callback_query(F.data == "check")
async def check(call: CallbackQuery):
    await interaction()

    if await is_member(call.from_user.id):
        await call.message.edit_text(
            "✅ Üyeliğin onaylandı!\n\n"
            "👑 SWAROVSKI menüsüne hoş geldin.",
            reply_markup=main_keyboard()
        )
        await call.answer("Üyelik başarılı!")
    else:
        await call.answer(
            "❌ Üç kanala da katılman gerekli!",
            show_alert=True
        )


@dp.chat_member()
async def member_update(event: ChatMemberUpdated):
    if event.chat.username not in [
        channel[1:] for channel in CHANNELS
    ]:
        return

    user_id = event.new_chat_member.user.id
    status = event.new_chat_member.status

    if status in ("left", "kicked"):
        try:
            await bot.send_message(
                user_id,
                "⚠️ Zorunlu kanallarımızdan birinden "
                "çıktın!\n\n"
                "Botu kullanmaya devam etmek için "
                "üç kanalımıza da tekrar katılman gerekli.",
                reply_markup=join_keyboard()
            )
        except Exception:
            pass


@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect("swarovski.db") as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users"
        )
        users = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT interactions FROM stats"
        )
        interactions_count = (await cursor.fetchone())[0]

    await message.answer(
        "👑 SWAROVSKI ADMIN PANELİ 👑\n\n"
        "📊 Bot İstatistikleri:\n"
        f"👥 Toplam Kullanıcı: {users}\n"
        f"💬 Toplam Etkileşim: {interactions_count}\n"
        "🔗 Toplam Başarılı Referans: 0 kişi\n\n"
        "🟢 Sistem Durumu: Aktif"
    )


async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN ayarlanmamış!")

    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())
