from flask import Flask, render_template_string
import os
import sqlite3

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Productivity Bot Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: white;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            color: #333;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 30px;
            text-align: center;
            font-size: 2.5em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            border: 2px solid #e9ecef;
        }
        .stat-value {
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        .instructions {
            background: #e8f4fc;
            padding: 25px;
            border-radius: 15px;
            margin-top: 30px;
            border-left: 5px solid #3498db;
        }
        .emoji-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        .emoji-item {
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 10px;
            border: 2px solid #ddd;
        }
        .emoji { font-size: 2.5em; }
        .btn {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            margin: 10px;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #764ba2;
            transform: translateY(-3px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Productivity Bot Dashboard</h1>
        
        <p style="text-align: center; font-size: 1.2em; margin-bottom: 30px;">
            Веб-панель для трекера продуктивности в Telegram
        </p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div>📊 Средний КПД</div>
                <div class="stat-value">{{ avg_efficiency }}%</div>
            </div>
            <div class="stat-card">
                <div>📅 Отслежено дней</div>
                <div class="stat-value">{{ days_count }}</div>
            </div>
            <div class="stat-card">
                <div>🏆 Идеальных дней</div>
                <div class="stat-value">{{ perfect_days }}</div>
            </div>
            <div class="stat-card">
                <div>✅ Продуктивных</div>
                <div class="stat-value">{{ productive_days }}</div>
            </div>
        </div>
        
        <h2 style="margin: 40px 0 20px; color: #2c3e50;">📝 Как пользоваться:</h2>
        
        <div class="emoji-grid">
            <div class="emoji-item">
                <div class="emoji">🤖</div>
                <div>Найдите бота в Telegram</div>
            </div>
            <div class="emoji-item">
                <div class="emoji">/start</div>
                <div>Начните диалог</div>
            </div>
            <div class="emoji-item">
                <div class="emoji">📅</div>
                <div>Нажмите "Сегодня"</div>
            </div>
            <div class="emoji-item">
                <div class="emoji">✅</div>
                <div>Отмечайте задачи</div>
            </div>
        </div>
        
        <div class="instructions">
            <h3 style="color: #2c3e50; margin-bottom: 15px;">⚡ Быстрый старт:</h3>
            <ol style="line-height: 1.8; padding-left: 20px;">
                <li>Откройте Telegram и найдите бота</li>
                <li>Отправьте команду <code>/start</code></li>
                <li>Нажмите кнопку "📅 Сегодня"</li>
                <li>Выбирайте выполненные задачи через кнопки</li>
                <li>Нажмите "✅ Рассчитать КПД"</li>
                <li>Смотрите статистику через "📊 Статистика"</li>
            </ol>
        </div>
        
        <div style="text-align: center; margin-top: 40px;">
            <a href="https://t.me/{{ bot_username }}" class="btn" target="_blank">
                🔗 Перейти к боту
            </a>
            <a href="/api/stats" class="btn" style="background: #27ae60;">
                📊 API статистики
            </a>
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #eee; text-align: center;">
            <p>🚀 Бот работает на Railway</p>
            <p style="color: #666; font-size: 0.9em; margin-top: 10px;">
                Обновлено: {{ updated_at }}
            </p>
        </div>
    </div>
</body>
</html>
"""

def get_stats():
    conn = sqlite3.connect('productivity.db')
    c = conn.cursor()
    
    # Общая статистика
    c.execute("SELECT COUNT(*) FROM days")
    days_count = c.fetchone()[0] or 0
    
    c.execute("SELECT AVG(efficiency) FROM days")
    avg_efficiency = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM days WHERE efficiency = 100")
    perfect_days = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM days WHERE efficiency >= 70")
    productive_days = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'days_count': int(days_count),
        'avg_efficiency': round(avg_efficiency, 1),
        'perfect_days': perfect_days,
        'productive_days': productive_days,
        'bot_username': os.environ.get('BOT_USERNAME', 'ProductivityTrackerBot'),
        'updated_at': 'Сегодня'
    }

@app.route('/')
def index():
    stats = get_stats()
    return render_template_string(HTML_TEMPLATE, **stats)

@app.route('/api/stats')
def api_stats():
    stats = get_stats()
    return stats

@app.route('/health')
def health():
    return {'status': 'ok', 'service': 'productivity-bot'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
