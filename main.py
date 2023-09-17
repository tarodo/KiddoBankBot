import dataclasses
import logging
import os
from enum import IntEnum, auto, StrEnum
from typing import Sequence, Type

from telegram import ReplyKeyboardRemove, Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          ConversationHandler, CallbackQueryHandler, MessageHandler, filters)
from environs import Env

env = Env()
env.read_env()

END = ConversationHandler.END

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class StateEnum(IntEnum):
    CHOOSING_ACT_ADMIN = auto()
    NEW_JUNIOR_NAME = auto()


class MainMenuAdminButtons(StrEnum):
    ADD_JUNIOR = "Add new Junior Saver"
    SHOW_ALL_JUNIORS = "Show all Juniors"


@dataclasses.dataclass
class InlineButton:
    name: str
    show_name: str


def make_keyboard(buttons: Sequence[str], number: int) -> ReplyKeyboardMarkup:
    keyboard = [
        buttons[btn_n : btn_n + number] for btn_n in range(0, len(buttons), number)
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    return markup


def get_menu_keyboard(button_enum: Type[StrEnum]) -> ReplyKeyboardMarkup:
    buttons = [button for button in button_enum]
    return make_keyboard(buttons, 2)


def make_inline_keyboard(
    buttons: Sequence[InlineButton], number: int, prefix=""
) -> InlineKeyboardMarkup:
    keyboard = []
    for btn_n in range(0, len(buttons), number):
        keyboard.append(
            [
                InlineKeyboardButton(btn.show_name, callback_data=f"{prefix}{btn.name}")
                for btn in buttons[btn_n : btn_n + number]
            ]
        )
    return InlineKeyboardMarkup(keyboard)


def get_inline_keyboard_from_enum(enum_collection: Type[StrEnum], number=3, prefix=""):
    buttons = [InlineButton(btn.value, btn.value) for btn in enum_collection]
    return make_inline_keyboard(buttons, number=number, prefix=prefix)


def is_admin(user_id: int) -> bool:
    from admins import admins
    if user_id in admins:
        return True


async def main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send first question for user"""
    user_id = update.message.from_user.id

    text = f"Hello my Lord! {user_id} What do you want from me? {is_admin(user_id)}"
    keyboard = get_inline_keyboard_from_enum(MainMenuAdminButtons)
    await update.message.reply_text(
        text,
        reply_markup=keyboard
    )
    return StateEnum.CHOOSING_ACT_ADMIN


async def add_new_junior(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    text = "What is the new user's name?"
    await query.edit_message_text(text=text, reply_markup=None)
    return StateEnum.NEW_JUNIOR_NAME


async def send_link_new_junior(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = f"Send next message to a new Junior"
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=text
    )
    bot = await context.bot.get_me()
    bot_username = bot.username
    link = f"https://t.me/{bot_username}?start=1111"
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=link
    )
    return StateEnum.CHOOSING_ACT_ADMIN


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Good by!", reply_markup=ReplyKeyboardRemove())

    return END


def main() -> None:
    """Run the bot."""
    bot_token = os.getenv("BOT_TOKEN")
    application = Application.builder().token(bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", main_menu)],
        states={
            StateEnum.CHOOSING_ACT_ADMIN: [
                CallbackQueryHandler(
                    add_new_junior, pattern=rf"^{MainMenuAdminButtons.ADD_JUNIOR}$"
                )
            ],
            StateEnum.NEW_JUNIOR_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_link_new_junior),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
