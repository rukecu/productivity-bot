import os
import telebot
from telebot import types
import datetime
import json
import sqlite3
from flask import Flask, request
import threading

# Конфигурация
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
PORT = int(os.environ.get('PORT', 5000))

bot = telebot.TeleBot(TOKEN)

# Инициализация Flask для вебхуков
app = Flask(__name__)

# Простая база данных в памяти (для демо)
user_data = {}

# Создаем SQLite базу
def init_db():
    conn = sqlite3.connect('productivity.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS days
                 (user_id INTEGER, date TEXT, sleep REAL, 
                  workout REAL, wakeup REAL, python REAL,
                  efficiency REAL)''')
    conn.commit()
    conn.close()

init_db()

def save_to_db(user_id, date, data):
    conn = sqlite3.connect('productivity.db')
    c = conn.cursor()
    efficiency = data.get('sleep', 0) + data.get('workout', 0) + data.get('wakeup', 0) + data.get('python', 0)
    
    c.execute('''INSERT OR REPLACE INTO days 
                 (user_id, date, sleep, workout, wakeup, python, efficiency)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (user_id, date, data.get('sleep', 0), data.get('workout', 0),
               data.get('wakeup', 0), data.get('python', 0), efficiency))
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    welcome = """
    🚀 *Productivity Tracker Bot*
    
    *Команды:*
    /today - Отметить сегодня
    /stats - Статистика
    /month - Таблица месяца
    /export - Экспорт данных
    /help - Помощь
    
    *Быстрые кнопки ниже ↓*
    """
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('📅 Сегодня', '📊 Статистика', '📈 Месяц', '💾 Экспорт')
    
    bot.send_message(message.chat.id, welcome, 
                     parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '📅 Сегодня')
def today_command(message):
    user_id = message.from_user.id
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['editing_date'] = today
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Сон
    markup.add(
        types.InlineKeyboardButton("🛌 7+ ч (30%)", callback_data="sleep_30"),
        types.InlineKeyboardButton("🛌 6-7 ч (15%)", callback_data="sleep_15"),
        types.InlineKeyboardButton("🛌 <6 ч (0%)", callback_data="sleep_0")
    )
    
    # Тренировка
    markup.row(
        types.InlineKeyboardButton("🏃 Полная (25%)", callback_data="workout_25"),
        types.InlineKeyboardButton("🚶 Короткая (12.5%)", callback_data="workout_12")
    )
    markup.row(types.InlineKeyboardButton("❌ Нет (0%)", callback_data="workout_0"))
    
    # Подъём
    markup.row(
        types.InlineKeyboardButton("☀️ До 10:00 (20%)", callback_data="wakeup_20"),
        types.InlineKeyboardButton("⏰ 10-11:00 (10%)", callback_data="wakeup_10"),
        types.InlineKeyboardButton("🌙 После 11:00 (0%)", callback_data="wakeup_0")
    )
    
    # Python
    markup.row(
        types.InlineKeyboardButton("🐍 1+ ч (25%)", callback_data="python_25"),
        types.InlineKeyboardButton("📚 30-60 мин (15%)", callback_data="python_15"),
        types.InlineKeyboardButton("📖 Теория (5%)", callback_data="python_5"),
        types.InlineKeyboardButton("❌ Нет (0%)", callback_data="python_0")
    )
    
    markup.row(types.InlineKeyboardButton("✅ Рассчитать КПД", callback_data="calculate"))
    
    bot.send_message(message.chat.id, 
                     f"📅 *{datetime.datetime.now().strftime('%d.%m.%Y')}*\n\n"
                     "Выберите выполненные задачи:", 
                     parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    if 'editing_date' not in user_data[user_id]:
        user_data[user_id]['editing_date'] = datetime.datetime.now().strftime('%Y-%m-%d')
    
    if 'tasks' not in user_data[user_id]:
        user_data[user_id]['tasks'] = {'sleep': 0, 'workout': 0, 'wakeup': 0, 'python': 0}
    
    data = call.data.split('_')
    
    if data[0] == 'sleep':
        user_data[user_id]['tasks']['sleep'] = float(data[1])
        bot.answer_callback_query(call.id, f"Сон: {data[1]}%")
        
    elif data[0] == 'workout':
        value = 25 if data[1] == '25' else 12.5 if data[1] == '12' else 0
        user_data[user_id]['tasks']['workout'] = value
        bot.answer_callback_query(call.id, f"Тренировка: {value}%")
        
    elif data[0] == 'wakeup':
        user_data[user_id]['tasks']['wakeup'] = float(data[1])
        bot.answer_callback_query(call.id, f"Подъём: {data[1]}%")
        
    elif data[0] == 'python':
        user_data[user_id]['tasks']['python'] = float(data[1])
        bot.answer_callback_query(call.id, f"Python: {data[1]}%")
        
    elif data[0] == 'calculate':
        tasks = user_data[user_id]['tasks']
        efficiency = tasks['sleep'] + tasks['workout'] + tasks['wakeup'] + tasks['python']
        
        # Сохраняем в базу
        save_to_db(user_id, user_data[user_id]['editing_date'], tasks)
        
        # Формируем результат
        result = f"""
📊 *КПД дня: {efficiency}%*

🛌 Сон: {tasks['sleep']}%
🏃 Тренировка: {tasks['workout']}%
☀️ Подъём: {tasks['wakeup']}%
🐍 Python: {tasks['python']}%

{'🏆 ИДЕАЛЬНЫЙ ДЕНЬ!' if efficiency == 100 else 
 '✅ Отлично!' if efficiency >= 70 else 
 '👍 Хорошо!' if efficiency >= 50 else 
 '💪 Завтра лучше!'}
        """
        
        bot.edit_message_text(result, call.message.chat.id, 
                             call.message.message_id, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '📊 Статистика')
def stats_command(message):
    user_id = message.from_user.id
    
    # Простая статистика
    conn = sqlite3.connect('productivity.db')
    c = conn.cursor()
    c.execute("SELECT AVG(efficiency) FROM days WHERE user_id = ?", (user_id,))
    avg = c.fetchone()[0] or 0
    conn.close()
    
    stats = f"""
📈 *Ваша статистика:*

Средний КПД: *{avg:.1f}%*
Отслежено дней: *{len([k for k in user_data.keys() if isinstance(k, int)])}*

*Советы:*
- Старайтесь спать 7+ часов
- Тренируйтесь через день
- Начинайте день до 10:00
- Уделяйте Python минимум 1 час
    """
    
    bot.send_message(message.chat.id, stats, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '📈 Месяц')
def month_command(message):
    # Простая таблица на 7 дней для демо
    table = """
📅 *Последние 7 дней:*

День | 🛌 | 🏃 | ☀️ | 🐍 | КПД
-----|----|----|----|----|----
Пн   | 🟢 | 🏃 | ☀️ | 🐍 | 85%
Вт   | 🟢 | ❌ | ⏰ | 📚 | 50%
Ср   | 🟡 | 🚶 | ☀️ | 🐍 | 72%
Чт   | 🟢 | 🏃 | ☀️ | ❌ | 75%
Пт   | ⚫ | 🏃 | 🌙 | 🐍 | 45%
Сб   | 🟢 | ❌ | ☀️ | 📖 | 55%
Вс   | 🟡 | 🚶 | ⏰ | 🐍 | 62%

📊 *Среднее: 63%*
    """
    
    bot.send_message(message.chat.id, table, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '💾 Экспорт')
def export_command(message):
    user_id = message.from_user.id
    
    # Генерируем простой CSV
    csv_data = "Дата;Сон%;Тренировка%;Подъём%;Python%;КПД%\n"
    
    conn = sqlite3.connect('productivity.db')
    c = conn.cursor()
    c.execute("SELECT * FROM days WHERE user_id = ?", (user_id,))
    
    for row in c.fetchall():
        csv_data += f"{row[1]};{row[2]};{row[3]};{row[4]};{row[5]};{row[6]}\n"
    
    conn.close()
    
    # Отправляем как файл
    bot.send_document(message.chat.id, 
                     ('productivity.csv', csv_data),
                     caption="📁 Ваши данные")

# Вебхук эндпоинты
@app.route('/')
def home():
    return "🚀 Productivity Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Bad request', 403

# Запуск Flask в отдельном потоке
def run_flask():
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    if WEBHOOK_URL:
        print("🌐 Using webhook mode...")
        bot.remove_webhook()
        bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        
        # Запускаем Flask в основном потоке
        run_flask()
    else:
        print("🤖 Using polling mode...")
        # Запускаем Flask в отдельном потоке
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        # Запускаем бота
        bot.polling(none_stop=True)
