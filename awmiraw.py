from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler, ContextTypes
import logging

# فعال سازی لاگ‌ها
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# وضعیت گفتگو
WAITING_FOR_REPLY = 1

# توکن ربات و آیدی ادمین
import os

TOKEN = os.getenv("8042479153:AAF-n-swq5r6HuOqC2r3Nm1zc1BzKwNdMwc")

ADMIN_CHAT_ID = 7316220906

# برای ذخیره کردن اطلاعات پیام ها
pending_replies = {}

# شروع کار
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋\nمیتونی اینجا به صورت ناشناس هرچی تو دلت هست یا حس و حالت رو باهام درمیون بزاری.")

# دریافت پیام‌های کاربر
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_message = update.message.text

    # پیام‌های خود ادمین رو پردازش نکن
    if user_id == ADMIN_CHAT_ID:
        return

    logger.info(f"پیام جدید دریافت شد: {user_message}")

    # دکمه پاسخ ساختن
    keyboard = [
        [InlineKeyboardButton("✉️ پاسخ به این پیام", callback_data=f"reply_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # پیام ناشناس برای ادمین بفرست
    sent_message = await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📨 پیام ناشناس جدید:\n\n{user_message}",
        reply_markup=reply_markup
    )

    # ذخیره اینکه به این کاربر باید جواب داده بشه
    pending_replies[user_id] = True

    # تایید به کاربر
    await update.message.reply_text("✅ پیامت به صورت ناشناس ارسال شد. منتظر پاسخ باش.")

# وقتی روی دکمه پاسخ کلیک میکنیم
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    if callback_data.startswith("reply_"):
        target_user_id = int(callback_data.split("_")[1])

        if pending_replies.get(target_user_id, False):
            # ذخیره موقت آیدی کاربر هدف
            context.user_data['target_user_id'] = target_user_id
            await query.edit_message_text("✍️ لطفاً پیام پاسخ خود را تایپ کنید:")
            return WAITING_FOR_REPLY
        else:
            await query.edit_message_text("❗ این پیام یا قبلاً پاسخ داده شده یا وجود ندارد.")
            return ConversationHandler.END

# دریافت متن پاسخ ادمین
async def receive_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'target_user_id' not in context.user_data:
        await update.message.reply_text("❗ شما هیچ پیامی برای پاسخ دادن انتخاب نکردید.")
        return ConversationHandler.END

    target_user_id = context.user_data.pop('target_user_id')
    reply_text = update.message.text

    # ارسال پاسخ به کاربر ناشناس
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"📝 پاسخ به پیامت:\n\n{reply_text}"
        )
        await update.message.reply_text("✅ پاسخ شما ارسال شد.")
    except Exception as e:
        logger.error(f"خطا در ارسال پاسخ: {e}")
        await update.message.reply_text("❗ خطا در ارسال پاسخ به کاربر.")

    # حذف از لیست pending
    pending_replies.pop(target_user_id, None)

    return ConversationHandler.END

# لغو عملیات
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

# ساخت اپلیکیشن
app = Application.builder().token(TOKEN).build()

# تنظیم هندلرها
conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button)],
    states={
        WAITING_FOR_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reply)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conversation_handler)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# اجرای ربات
if __name__ == "__main__":
    import asyncio
    import sys

    if sys.platform.startswith('win') and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("✅ ربات با موفقیت روشن شد")
    app.run_polling()
 