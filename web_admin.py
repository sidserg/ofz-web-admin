from flask import Flask, request, redirect, url_for, render_template_string
from pages.status import get_status_html
from pages.schedule import get_schedule_html

app = Flask(__name__)
# Логин и пароль для доступа (измените на свои)




app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>OFZ PRO</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Arial, sans-serif; background: #f4f6f9; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 200px; background: #2c3e50; color: white; display: flex; flex-direction: column; flex-shrink: 0; }
        .sidebar h1 { font-size: 18px; text-align: center; padding: 20px 0; background: #1a252f; margin: 0; color: #1abc9c; }
        .sidebar a { padding: 15px; text-decoration: none; color: #bdc3c7; border-left: 4px solid transparent; }
        .sidebar a:hover, .sidebar a.active { background: #34495e; color: white; border-left-color: #1abc9c; }
        .main { flex-grow: 1; padding: 20px; overflow-y: auto; background: #f4f6f9; }
        .content { background: white; padding: 20px; border-radius: 5px; }
        h2 { font-size: 18px; font-weight: bold; margin: 15px 0 5px 0; color: #000; }
        p { margin: 3px 0; font-size: 15px; color: #000; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { padding: 2px 0; font-size: 15px; color: #000; }
        input[type="number"] { padding: 8px; font-size: 16px; width: 70px; border: 1px solid #ccc; border-radius: 4px; margin: 0 5px; }
        button { padding: 10px 20px; font-size: 16px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 15px; }
        label { display: inline-block; margin-bottom: 10px; font-size: 16px; }
        .schedule-row { margin-bottom: 15px; padding: 10px; border-radius: 5px; }
        .schedule-row.active { background: #f0f8ff; }
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
    </div>
    <div class="main">
        <div class="content">
            {{ content|safe }}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return redirect(url_for('status_page'))

@app.route('/status')
def status_page():
    try:
        content = get_status_html()
    except Exception as e:
        content = f"<h2 style='color:red'>Ошибка загрузки: {e}</h2>"
    return render_template_string(HTML, content=content, request=request)

@app.route('/schedule', methods=['GET', 'POST'])
def schedule_page():
    try:
        content = get_schedule_html(request)
    except Exception as e:
        content = f"<h2 style='color:red'>Ошибка расписания: {e}</h2>"
    return render_template_string(HTML, content=content, request=request)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
