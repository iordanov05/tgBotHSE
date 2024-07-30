import telebot
from telebot import types
import os
from dotenv import load_dotenv
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import traceback
import re
# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Загрузка переменных среды из .env файла
load_dotenv()
# Получение API токена Telegram из переменной среды
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
# Получение пути к учетным данным Google Sheets из переменной среды
GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
# Получение имени Google Sheets из переменной среды
GOOGLE_SHEETS_NAME = os.getenv('GOOGLE_SHEETS_NAME')
GOOGLE_SHEETS_US = os.getenv('GOOGLE_SHEETS_US')


bot = telebot.TeleBot(API_TOKEN)

# Настройка доступа к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
client = gspread.authorize(creds)

sheet_U = client.open(GOOGLE_SHEETS_US).worksheet('Users')
sheet_S = client.open(GOOGLE_SHEETS_US).worksheet('smart_guys')
# Открытие листа "A"
sheet_A = client.open(GOOGLE_SHEETS_NAME).worksheet('A')
# Открытие листа "B"
sheet_B = client.open(GOOGLE_SHEETS_NAME).worksheet('B')
# Открытие листа "C"
sheet_C = client.open(GOOGLE_SHEETS_NAME).worksheet('C')

def check_room_format(string):
    pattern = r'^[a-c]((0[1-9])|(1[0-9])|(2[0-5]))[1-4]\(\d{1,4}\)$' 
    if re.match(pattern, string):
        return True
    else:
        return False
    
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    telegram_profile = f"https://t.me/{message.chat.username}"
    try:
        sheet_U.append_row([telegram_profile])
    except Exception as e:
        logger.error(f"Ошибка при добавлении ID пользователя в Google Sheets: {e}")
    welcome_text = (
         f" Привет! Поздравляю с поступлением в НИУ ВШЭ! Если тебе пришло письмо о расселении, в котором говорится, что ты будешь проживать в Общежитии №8 'Трилистник', я могу помочь узнать, в какой квартире и комнате именно ты будешь жить. Просто отправь мне номер своей комнаты точно так, как в сообщении, которое ты получил (например, <b>B000(0)</b>), и я расскажу тебе все подробности.  "
    )
    bot.send_message(chat_id, welcome_text,parse_mode='html')
    bot.register_next_step_handler(message, room_definition)

@bot.message_handler(content_types=['text', 'photo', 'audio', 'document', 'sticker', 'video', 'voice', 'video_note', 'location', 'contact', 'new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo', 'delete_chat_photo', 'group_chat_created', 'supergroup_chat_created', 'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message'])
def handle_message(message):
    telegram_profile = f"https://t.me/{message.chat.username}"
    user_input = message.text.lower() if message.text else None
    if check_room_format(user_input):
        room_definition(message)
    elif user_input in ["b000(0)", "a000(0)", "c000(0)"]:
        bot.send_photo(message.chat.id, photo=open('mem.jpg', 'rb'), caption="Пожалуйста, перепроверьте сообщение, которое вы получили, и укажите реальный номер комнаты.")
        try:
            sheet_S.append_row([telegram_profile])
        except Exception as e:
            logger.error(f"Ошибка при добавлении ID пользователя в Google Sheets: {e}")
    else:
        correct_input(message)
 
 
def correct_input(message):
    bot.send_message(message.chat.id, 
         "Пожалуйста, укажите мне номер своей комнаты точно так, как он указан в сообщении, которое вы получили (например, <b>B000(0)</b>), и я с удовольствием предоставлю вам все необходимые подробности.",
         parse_mode='html'
         )
    bot.register_next_step_handler(message,room_definition)       
def room_definition(message):
    telegram_profile = f"https://t.me/{message.chat.username}"
    if message.text.lower() in ["b000(0)", "a000(0)", "c000(0)"]:
        bot.send_photo(message.chat.id, photo=open('memi-klev-club-m9ei-p-memi-samii-umnii-chelovek-28.jpg', 'rb'), caption="Пожалуйста, перепроверьте сообщение, которое вы получили, и укажите реальный номер комнаты.")
        try:
            sheet_S.append_row([telegram_profile])
        except Exception as e:
            logger.error(f"Ошибка при добавлении ID пользователя в Google Sheets: {e}")
    elif (len(message.text) == 7 and check_room_format(message.text.lower())):
        try:    
            letter = message.text.lower()[0]
            storey = int(message.text.lower()[1:3])
            apartment = int(message.text.lower()[3])
            room = int(message.text.lower()[5])
            if letter == 'a':
                sheet = sheet_A
            elif letter == 'b':
                sheet = sheet_B
            elif letter == 'c':
                sheet = sheet_C
            rooms = sheet.col_values(int(apartment))[1:]
            room_info = f"В квартире есть {len(rooms)} комнаты:\n"
            room_info += ';\n'.join([f"• комната для {num} человек" for num in rooms])
            room_info += ".\n"
            if not '2-3' in rooms:
                total_capacity = sum(int(capacity) for capacity in rooms)
                room_capacity = rooms[room-1]
            else:
                room_capacity = rooms[room-1]
                rooms[0]='2'
                total_capacity = sum(int(capacity) for capacity in rooms)
                total_capacity = f"{total_capacity}-{total_capacity+1}"
            
            # logger.info(f"Обработано сообщение от пользователя {message.from_user.id}: {message.text}")
            # logger.info(f"Найден лист Google Sheets для буквы {letter}: {sheet}")
            # logger.info(f"Информация о квартире: корпус {letter.upper()}, этаж {storey}, квартира номер {apartment}")
            # logger.info(f"Информация о комнатах в квартире: {room_info}")
            # logger.info(f"Общая вместимость квартиры: {total_capacity}")
            # logger.info(f"Обработана информация о комнате: номер комнаты {room}, вместимость {room_capacity} человек")

            answer = (
                f'''Ты будешь жить в корпусе {letter.upper()} на {storey} этаже, в квартире номер {apartment}.\n\n{room_info}\nВсего в квартире будут жить {total_capacity} человек.\n\nТвоя комната — номер {room}, рассчитанная на {room_capacity} человек. \nДобро пожаловать и приятно познакомиться! 🏡😊
                ''')
            bot.send_message(message.chat.id,answer,parse_mode='html' )
        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
            logger.error(traceback.format_exc())
            correct_input(message)
    else:
        correct_input(message)
        
        
if __name__ == '__main__':
    # Получение информации о боте
    bot_info = bot.get_me()
    # Логирование информации о боте
    logger.info(f"Connected bot: {bot_info.first_name} [@{bot_info.username}]")
    while True:
        try:
            logger.info("Starting bot polling...")
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            logger.info("Restarting bot in 10 seconds...")
            time.sleep(10)