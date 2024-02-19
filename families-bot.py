from telegram import Update, ForceReply, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN
import logging
import asyncio

Netflix_lst, Grammarly_lst, Spotify_lst, Beeline_lst, GPT_lst, Yandex_lst = [], [], [], [], [], []
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
lock = asyncio.Lock()

service_lists = {
    "Netflix": Netflix_lst,
    "Grammarly": Grammarly_lst,
    "Spotify": Spotify_lst,
    "Beeline": Beeline_lst,
    "GPT": GPT_lst,
    "Yandex+": Yandex_lst,
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("Join Netflix"), KeyboardButton("Join Grammarly")],
        [KeyboardButton("Join Spotify"), KeyboardButton("Join Beeline")],
        [KeyboardButton("Join GPT"), KeyboardButton("Join Yandex+")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose the service where you want to find a family:", reply_markup=reply_markup)

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Provide a keyboard for service selection for joining
    keyboard = [
        [KeyboardButton("Join Netflix"), KeyboardButton("Join Grammarly")],
        [KeyboardButton("Join Spotify"), KeyboardButton("Join Beeline")],
        [KeyboardButton("Join GPT"), KeyboardButton("Join Yandex+")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Choose the service you want to join:", reply_markup=reply_markup)


async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Provide a keyboard for service selection for leaving
    keyboard = [
        [KeyboardButton("Leave Netflix"), KeyboardButton("Leave Grammarly")],
        [KeyboardButton("Leave Spotify"), KeyboardButton("Leave Beeline")],
        [KeyboardButton("Leave GPT"), KeyboardButton("Leave Yandex+")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Choose the service family you want to leave:", reply_markup=reply_markup)

async def handle_service_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    action, service_choice = update.message.text.split(" ", 1)  # Split text into action and service_choice

    # Define account limits for each service
    account_limits = {
        "Netflix": 4,
        "Grammarly": 5,
        "Spotify": 6,
        "Beeline": 5,
        "GPT": 4,
        "Yandex+": 8,
    }

    if service_choice in service_lists:
        selected_list = service_lists[service_choice]
        user_data = {'name': user.username if user.username else user.first_name, 'chat_id': chat_id}

        async with lock:
            if action == "Join":
                if user_data not in selected_list:
                    selected_list.append(user_data)
                    logger.info(f"User {user_data['name']} joined the {service_choice} list.")
                    # Notify all current list members about the new addition
                    await notify_members(context, selected_list, service_choice, account_limits, action="joined", new_member=user_data['name'])
                    
                    if len(selected_list) == account_limits[service_choice]:
                        # Notify users in the group that the family has been created
                        members = ", ".join([f"@{user['name']}" for user in selected_list])
                        message = f"{service_choice} Family of {len(selected_list)} created!\nMembers: {members}\nPlease write your family members to set up the plan!"
                        for user in selected_list:
                            await context.bot.send_message(chat_id=user['chat_id'], text=message)
                            logger.info(f"Family created notification sent to {user['name']} for {service_choice}.")

                        # Clear the list for the next group
                        selected_list.clear()
                        logger.info(f"The {service_choice} list has been cleared after forming a family.")
                else:
                    await context.bot.send_message(chat_id=chat_id, text="You are already in the family for this service")
                    logger.warning(f"User {user_data['name']} attempted to join the {service_choice} list but was already present.")
            
            elif action == "Leave":
                if user_data in selected_list:
                    selected_list.remove(user_data)
                    logger.info(f"User {user_data['name']} left the {service_choice} list.")
                    await context.bot.send_message(chat_id=chat_id, text=f"You left the {service_choice} family")
                    # Notify all current list members about the removal
                    await notify_members(context, selected_list, service_choice, account_limits, action="left", new_member=user_data['name'])
                else:
                    await context.bot.send_message(chat_id=chat_id, text=f"You are not in the family for this service")
                    logger.warning(f"User {user_data['name']} attempted to leave the {service_choice} list but was not found.")
    else:
        await context.bot.send_message(chat_id=chat_id, text="Invalid service choice.")
        logger.error(f"Invalid service choice received: {service_choice}")

async def notify_members(context, selected_list, service_choice, account_limits, action, new_member):
    members = ", ".join([f"@{user['name']}" for user in selected_list])
    left_to_find = account_limits[service_choice] - len(selected_list)
    # Notify all current list members about the update
    for member in selected_list:
        update_message = f"@{new_member} has {action} the {service_choice} family\nMembers list: {members}\nTotal allowed members amount: {account_limits[service_choice]}\nMembers left to find: {left_to_find}"
        await context.bot.send_message(chat_id=member['chat_id'], text=update_message)
        logger.info(f"Notification sent to {member['name']} about update in {service_choice} list.")



def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("leave", leave))
    application.add_handler(MessageHandler(filters.TEXT & (filters.Regex(r'^Join ') | filters.Regex(r'^Leave ')), handle_service_choice))

    application.run_polling()

if __name__ == "__main__":
    main()
