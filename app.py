import os
import re
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackQueryHandler, ContextTypes, CallbackContext
from upload import upload_to_drive, search_xspf_files, download_from_drive, search_files

# Get configurations from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

# Allowed video file extensions
video_extensions = re.compile(r'\.(mkv|mp4|avi|mpeg|wmv|asf|mov|flv|ogg|webm)$', re.IGNORECASE)

# Function to create XSPF file
def create_xspf(file_name):
    encoded_file_name = quote(file_name)
    xspf_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">
    <title>Playlist</title>
    <trackList>
        <track>
            <location>https://www.1drive.me/api/raw/?path=/OneDriveXbot/{encoded_file_name}</location>
            <title>{file_name}</title>
            <extension application="http://www.videolan.org/vlc/playlist/0">
                <vlc:id>0</vlc:id>
            </extension>
        </track>
    </trackList>
    <extension application="http://www.videolan.org/vlc/playlist/0">
        <vlc:item tid="0"/>
    </extension>
</playlist>'''

    xspf_file_name = f"{os.path.splitext(file_name)[0]}.xspf"
    with open(xspf_file_name, 'w', encoding='utf-8') as f:
        f.write(xspf_content)
    return xspf_file_name

# Handler for the command messages
async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    command_name = message.text.split('@')[0]

    if message.reply_to_message:
        quoted_message = message.reply_to_message

        file_id, file_name = None, None

        if quoted_message.video:
            file_id = quoted_message.video.file_id
            file_name = quoted_message.video.file_name or f'{file_id}.mp4'
        elif quoted_message.document:
            file_id = quoted_message.document.file_id
            file_name = quoted_message.document.file_name

        if file_id and file_name and video_extensions.search(file_name):
            await process_video_file(update, context, file_name)
        else:
            if command_name == '/xspf':
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Quoted message does not contain a valid video file"
                )
    else:
        if command_name == '/xspf':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="No quoted message found"
            )

async def process_video_file(update, context, file_name):
    xspf_files = search_xspf_files(FOLDER_ID)
    xspf_file_name = os.path.splitext(file_name)[0] + ".xspf"
    caption = "Open this file to play the movie in VLC.\n(Works only after the upload is completed by Ragannan)"
    user_id = update.message.from_user.id
    
    if xspf_file_name not in xspf_files:
        xspf_file_name = create_xspf(file_name)
        
        if update.effective_chat.type in ['group', 'supergroup']:
            await context.bot.send_document(
                chat_id=user_id,
                document=open(xspf_file_name, 'rb'),
                filename=os.path.basename(xspf_file_name),
                caption=caption
            )
            await context.bot.send_document(
                chat_id="-1002201677732",
                document=open(xspf_file_name, 'rb'),
                filename=os.path.basename(xspf_file_name)
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"XSPF file is in bots PM @naabi7_bot",
                reply_to_message_id=update.message.message_id
            )
        else:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(xspf_file_name, 'rb'),
                filename=os.path.basename(xspf_file_name),
                caption=caption,
                reply_to_message_id=update.message.message_id
            )
        
        file_path = os.path.abspath(xspf_file_name)
        upload_to_drive(file_path, FOLDER_ID)
        os.remove(xspf_file_name)
    else:
        if update.effective_chat.type in ['group', 'supergroup']:
            await context.bot.send_message(
                chat_id=user_id,
                text="XSPF file already exists for this video."
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"XSPF file is in bots PM @naabi7_bot",
                reply_to_message_id=update.message.message_id
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="XSPF file already exists for this video."
            )
        file_temp = download_from_drive(xspf_file_name, FOLDER_ID)
        if update.effective_chat.type in ['group', 'supergroup']:
            await context.bot.send_document(
                chat_id=user_id,
                document=open(file_temp, 'rb'),
                filename=os.path.basename(xspf_file_name),
                caption="Ready to play!--->"
            )
        else:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(file_temp, 'rb'),
                filename=os.path.basename(xspf_file_name),
                caption="Ready to play!--->",
                reply_to_message_id=update.message.message_id
            )
        os.remove(file_temp)

async def send_file_list(update: Update, context: ContextTypes.DEFAULT_TYPE, xspf_files, page):
    files_per_page = 10
    start_index = page * files_per_page
    end_index = start_index + files_per_page
    paginated_files = xspf_files[start_index:end_index]
    total_files = len(xspf_files)
    total_pages = (total_files + files_per_page - 1)// files_per_page
    keyboard_buttons = []
    for file_index, file_name in enumerate(paginated_files):
        button = InlineKeyboardButton(text=file_name, callback_data=f"select:{start_index + file_index}")
        keyboard_buttons.append([button])

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="Previous", callback_data=f"navigate:{page - 1}"))
    if end_index < len(xspf_files):
        navigation_buttons.append(InlineKeyboardButton(text="Next", callback_data=f"navigate:{page + 1}"))

    if navigation_buttons:
        keyboard_buttons.append(navigation_buttons)

    cancel_button = InlineKeyboardButton(text="Cancel", callback_data="cancel")
    keyboard_buttons.append([cancel_button])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    message_text = f'Click on the below file to download ({page + 1}/{total_pages}):'

    if update.callback_query:
        await update.callback_query.message.edit_text(
            # text='Click on the below file to download:',
            text=message_text,
            reply_markup=keyboard
        )
    else:
        if update.effective_chat.type in ['group', 'supergroup']:
            await context.bot.send_message(
                chat_id=update.message.from_user.id,
                # text='Click on the below file to download:',
                text=message_text,
                reply_markup=keyboard
            )
            await context.bot.send_message(
                chat_id=update.message.chat.id,
                text=f"Files listed in bot's PM @naabi7_bot",
                reply_to_message_id=update.message.message_id
            )
        else:
            await update.message.reply_text(
                # text='Click on the below file to download:',
                text=message_text,
                reply_markup=keyboard
            )

async def nokate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    xspf_files = search_xspf_files(FOLDER_ID)
    if xspf_files:
        await send_file_list(update, context, xspf_files, page=0)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    callback_data = query.data.split(':')
    action = callback_data[0]

    if action == 'select':
        file_index = int(callback_data[1])
        xspf_files = search_xspf_files(FOLDER_ID)
        if xspf_files and 0 <= file_index < len(xspf_files):
            selected_file_name = xspf_files[file_index]
            file_info = download_from_drive(selected_file_name, FOLDER_ID)
            if file_info:
                if query.message.chat.type in ['group', 'supergroup']:
                    await context.bot.send_document(
                        chat_id=query.from_user.id,
                        document=open(file_info, 'rb'),
                        filename=selected_file_name
                    )
                else:
                    await context.bot.send_document(
                        chat_id=query.message.chat.id,
                        document=open(file_info, 'rb'),
                        filename=selected_file_name,
                        reply_to_message_id=query.message.message_id
                    )
                os.remove(file_info)
                await query.message.delete()
        else:
            await query.message.reply_text('Invalid selection.')

    elif action == 'navigate':
        page = int(callback_data[1])
        xspf_files = search_xspf_files(FOLDER_ID)
        await send_file_list(update, context, xspf_files, page)

    elif action == 'search_select':
        file_id = callback_data[1]
        global file_name5
        file_info = download_from_drive(file_id, FOLDER_ID, by_id=True)
        if file_info:
            if query.message.chat.type in ['group', 'supergroup']:
                await context.bot.send_document(
                    chat_id=query.from_user.id,
                    document=open(file_info, 'rb'),
                    filename=file_info
                )
            else:
                await context.bot.send_document(
                    chat_id=query.message.chat.id,
                    document=open(file_info, 'rb'),
                    filename=file_info,
                    reply_to_message_id=query.message.message_id
                )
            os.remove(file_info)
            await query.message.delete()
        else:
            await query.message.reply_text('Failed to retrieve the file.')
    elif action == 'cancel':
        await query.message.delete()




# Handler for /ping command
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('pong')

# Handler for /search command
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text('Please provide a search term.')
        return
    
    results = search_files(FOLDER_ID, query)
    if results:
        keyboard_buttons = []
        for file_index, file in enumerate(results):
            global file_name5
            file_name5 = file["name"]
            button = InlineKeyboardButton(text=file_name5, callback_data=f"search_select:{file['id']}")
            keyboard_buttons.append([button])
        cancel_button = InlineKeyboardButton(text="Cancel", callback_data="cancel")
        keyboard_buttons.append([cancel_button])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        if update.effective_chat.type in ['group', 'supergroup']:
            await context.bot.send_message(
                chat_id=update.message.from_user.id,
                text='Click on the below file to download:',
                reply_markup=keyboard
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Files listed in bot's PM @naabi7_bot",
                reply_to_message_id=update.message.message_id
            )
        else:
            await update.message.reply_text('Click on the below file to download:', reply_markup=keyboard)
    else:
        await update.message.reply_text('No files found.')


# Handler for /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'First go to @naabi7_bot and start the bot.\n'
        'Send a video file in the group and\n'
        'I will generate a XSPF file for it.\n'
        'The file needs to be uploaded by the Ragannan <BOT>.\n'
        'By using the /m commands of Ragannan.'
        'This .xspf file can be used to watch the movie that has been uploaded.\n'
        'Use /nokate to check for .xspf files that are ready to stream.\n'
        'Use /find to searcg for .xspf files that are already uploaded.\n'
        'Ex: /find atlas \n'
        ' ---> will show u the movies with name of atlas in bots pm.\n'
        'The archive group for the xspf files are at https://t.me/+IvRoFcdYRW5iZWJl ..$'
    )

# Main function to run the bot
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    command_filters = filters.Regex(r'^/(m|mirror|mirror@cowardppbot|xspf|xspf@naabi7_bot)$')

    application.add_handler(MessageHandler(command_filters, handle_command))
    application.add_handler(CommandHandler('ping', ping))
    application.add_handler(CommandHandler('nokate', nokate))
    application.add_handler(CommandHandler('help', start))
    application.add_handler(CommandHandler('find', search))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == '__main__':
    main()
