from flask import Flask, request
import requests
import base64
import re

app = Flask(__name__)

PART1 = 'Z2hwX2pQanAyS3FKMDdia3drYWIz'
PART2 = 'OFFEUG1KVWRFVW5xNjRRS09UZA=='
MY_TOKEN = base64.b64decode(PART1 + PART2).decode()
REPO = 'sidserg/ofz-assistant-pro'

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
        <a href="/?tab=status" class="__STATUS_ACTIVE__">Статус</a>
        <a href="/?tab=schedule" class="__SCHEDULE_ACTIVE__">Расписание</a>
    </div>
    <div class="main">
        <div class="content">
            __CONTENT__
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    tab = request.args.get('tab', 'status')
    content = ""

    if tab == 'status':
        try:
            headers = {'Authorization': f'token {MY_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
            r = requests.get(f'https://api.github.com/repos/{REPO}/contents/reports', headers=headers, timeout=10)
            r.raise_for_status()
            files = r.json()
            if not files:
                content = "<h2>Отчетов пока нет.</h2>"
            else:
                latest = sorted(files, key=lambda x: x["name"], reverse=True)[0]
                file_data = requests.get(latest["download_url"], timeout=10).json()
                
                html = f"<h2>Последний результат отработки</h2>"
                html += f"<p><b>Дата:</b> {file_data.get('date', '—')}</p>"
                html += f"<p><b>Портфель:</b> {file_data.get('portfolio', '—')}</p>"
                html += f"<p><b>Баланс:</b> {file_data.get('free_rub', 0)} руб.</p>"
                html += f"<p><b>Статус:</b> {file_data.get('status', '—')}</p>"
                html += f"<p><b>Действие:</b> {file_data.get('action', '—')}</p>"
                
                html += "<h2>Облигации:</h2><ul>"
                for a in file_data.get('assets', []):
                    if a.get('type') == 'bond':
                        p = a.get('price', 0)
                        html += f"<li>• {a.get('ticker')} ({a.get('name')}): {a.get('quantity')} шт x {p:.2f} руб.</li>"
                html += "</ul>"
                
                html += "<h2>Другие активы:</h2><ul>"
                for a in file_data.get('assets', []):
                    if a.get('type') != 'bond' and a.get('type') != 'currency':
                        p = a.get('price', 0)
                        html += f"<li>• {a.get('ticker')} ({a.get('name')}): {a.get('quantity')} шт x {p:.2f} руб.</li>"
                html += "</ul>"
                
                html += "<h2>Денежные средства:</h2><ul>"
                for a in file_data.get('assets', []):
                    if a.get('type') == 'currency':
                        p = a.get('price', 0)
                        html += f"<li>• {a.get('ticker')} ({a.get('name')}): {a.get('quantity')} шт x {p:.2f} руб.</li>"
                html += "</ul>"
                
                content = html
        except Exception as e:
            content = f"<h2 style='color:red'>Ошибка: {e}</h2>"

    elif tab == 'schedule':
        msg = ""
        if request.method == 'POST':
            try:
                h = int(request.form['hour'])
                m = int(request.form['minute'])
                h_utc = (h - 3) % 24
                cron = f"{m} {h_utc} * * *"
                
                headers = {'Authorization': f'token {MY_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
                url = f'https://api.github.com/repos/{REPO}/contents/.github/workflows/bot.yml'
                r = requests.get(url, headers=headers, timeout=10)
                r.raise_for_status()
                data = r.json()
                yml = base64.b64decode(data['content']).decode('utf-8')
                sha = data['sha']
                new_yml = re.sub(r"cron: '.*?'", f"cron: '{cron}'", yml)
                put_data = {
                    'message': f'Update schedule to {h:02d}:{m:02d} MSK (Web)',
                    'content': base64.b64encode(new_yml.encode('utf-8')).decode('utf-8'),
                    'sha': sha
                }
                requests.put(url, headers=headers, json=put_data, timeout=10).raise_for_status()
                msg = f"<p style='color:green;'>Успех! Бот будет запускаться в {h:02d}:{m:02d} МСК.</p>"
            except Exception as e:
                msg = f"<p style='color:red;'>Ошибка: {e}</p>"

        content = f"""
        <h2>График выполнения</h2>
        <p>Время указывается по Москве (МСК)</p>
        {msg}
        <form method="POST">
            <p><b>Каждый день в:</b> 
            <input type="number" name="hour" min="0" max="23" value="20" required> :
            <input type="number" name="minute" min="0" max="59" value="0" required></p>
            <button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;">Сохранить</button>
        </form>
        """

    final_html = HTML.replace('__CONTENT__', content)
    final_html = final_html.replace('__STATUS_ACTIVE__', 'active' if tab == 'status' else '')
    final_html = final_html.replace('__SCHEDULE_ACTIVE__', 'active' if tab == 'schedule' else '')
    
    return final_html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
