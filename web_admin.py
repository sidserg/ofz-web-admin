from flask import Flask, request, redirect, url_for, render_template_string
from pages.status import get_status_html
from pages.schedule import get_schedule_html
from pages.settings import get_settings_html
from pages.calendar import get_calendar_html

app = Flask(__name__)

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Вход - OFZ PRO</title>
    <style>
        body { font-family: Arial; background: #2c3e50; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: white; padding: 40px; border-radius: 8px; text-align: center; }
        input { padding: 10px; font-size: 18px; margin-bottom: 20px; width: 200px; text-align: center; }
        button { padding: 10px 30px; font-size: 18px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Введите пароль</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Пароль" required><br>
            <button type="submit">Войти</button>
        </form>
    </div>
</body>
</html>
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>OFZ PRO</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Arial, sans-serif; background: #f4f6f9; display: flex; height: 100vh; overflow: hidden; font-weight: 500; }
        .sidebar { width: 200px; background: #2c3e50; color: white; display: flex; flex-direction: column; flex-shrink: 0; }
        .sidebar h1 { font-size: 18px; text-align: center; padding: 20px 0; background: #1a252f; margin: 0; color: #1abc9c; }
        .sidebar a { padding: 15px; text-decoration: none; color: #bdc3c7; border-left: 4px solid transparent; font-weight: 600; }
        .sidebar a:hover, .sidebar a.active { background: #34495e; color: white; border-left-color: #1abc9c; }
        .main { flex-grow: 1; padding: 20px; overflow-y: auto; background: #f4f6f9; }
        .content { background: white; padding: 20px; border-radius: 5px; }
        h2 { font-size: 18px; font-weight: 900; margin: 15px 0 5px 0; color: #000; }
        p { margin: 3px 0; font-size: 15px; color: #000; font-weight: 600; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { padding: 2px 0; font-size: 15px; color: #000; font-weight: 600; }
        input[type="number"] { padding: 5px; font-size: 14px; width: 60px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 20px; font-size: 16px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        @media (max-width: 600px) {
            body { flex-direction: column; }
            .sidebar { width: 100%; flex-direction: row; overflow-x: auto; }
            .sidebar h1 { display: none; }
            .sidebar a { border-left: none; border-bottom: 4px solid transparent; white-space: nowrap; }
            .sidebar a.active { border-bottom-color: #1abc9c; }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <h1>OFZ PRO</h1>
        <a href="/status" class="{{ 'active' if request.path == '/status' else '' }}">Статус</a>
        <a href="/schedule" class="{{ 'active' if request.path == '/schedule' else '' }}">Расписание</a>
        <a href="/settings" class="{{ 'active' if request.path == '/settings' else '' }}">Настройки</a>
        <a href="/calendar" class="{{ 'active' if request.path == '/calendar' else '' }}">Календарь</a>
    </div>
    <div class="main">
        <div class="content">
            {{ content|safe }}
        </div>
    </div>
</body>
</html>
"""

def check_auth():
    return request.cookies.get('auth_token') == 'secret_007'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == '007':
            resp = redirect(url_for('index'))
            resp.set_cookie('auth_token', 'secret_007', max_age=86400*30)
            return resp
        else:
            return HTML_LOGIN.replace('</h2>', '</h2><p style="color:red">Неверный пароль</p>')
    return HTML_LOGIN

@app.route('/')
def index():
    if not check_auth():
        return redirect(url_for('login'))
    return redirect(url_for('status_page'))

@app.route('/status')
def status_page():
    if not check_auth():
        return redirect(url_for('login'))
    try:
        content = get_status_html()
    except Exception as e:
        content = f"<h2 style='color:red'>Ошибка загрузки: {e}</h2>"
    return render_template_string(HTML, content=content, request=request)

@app.route('/schedule', methods=['GET', 'POST'])
def schedule_page():
    if not check_auth():
        return redirect(url_for('login'))
    try:
        content = get_schedule_html(request)
    except Exception as e:
        content = f"<h2 style='color:red'>Ошибка расписания: {e}</h2>"
    return render_template_string(HTML, content=content, request=request)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    if not check_auth():
        return redirect(url_for('login'))
    try:
        content = get_settings_html(request)
    except Exception as e:
        content = f"<h2 style='color:red'>Ошибка настроек: {e}</h2>"
    return render_template_string(HTML, content=content, request=request)

@app.route('/calendar')
def calendar_page():
    if not check_auth():
        return redirect(url_for('login'))
    try:
        content = get_calendar_html(request)
    except Exception as e:
        content = f"<h2 style='color:red'>Ошибка календаря: {e}</h2>"
    return render_template_string(HTML, content=content, request=request)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
