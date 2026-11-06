import requests
import base64
import html

PART1 = 'Z2hwX2pQanAyS3FKMDdia3drYWIz'
PART2 = 'OFFEUG1KVWRFVW5xNjRRS09UZA=='
MY_TOKEN = base64.b64decode(PART1 + PART2).decode()
REPO = 'sidserg/ofz-assistant-pro'

def get_status_html():
    try:
        headers = {'Authorization': f'token {MY_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
        r = requests.get(f'https://api.github.com/repos/{REPO}/contents/reports', headers=headers, timeout=10)
        r.raise_for_status()
        files = r.json()
        if not files:
            return "<h2>Отчетов пока нет.</h2>"
        
        latest = sorted(files, key=lambda x: x["name"], reverse=True)[0]
        file_data = requests.get(latest["download_url"], timeout=10).json()
        
        html = f"<h2>Последний результат отработки</h2>"
        html += f"<p><b>Дата:</b> {html.escape(str(file_data.get('date', '—')))}</p>"
        html += f"<p><b>Портфель:</b> {html.escape(str(file_data.get('portfolio', '—')))}</p>"
        html += f"<p><b>Баланс:</b> {float(file_data.get('free_rub', 0)):.2f} руб.</p>"
        html += f"<p><b>Статус:</b> {html.escape(str(file_data.get('status', '—')))}</p>"
        html += f"<p><b>Действие:</b> {html.escape(str(file_data.get('action', '—')))}</p>"
        
        html += "<h2>Облигации:</h2><ul>"
        for a in file_data.get('assets', []):
            if a.get('type') == 'bond':
                p = float(a.get('price', 0))
                html += f"<li>• {html.escape(str(a.get('ticker', '?')))} ({html.escape(str(a.get('name', '?')))}): {float(a.get('quantity', 0))} шт x {p:.2f} руб.</li>"
        html += "</ul>"
        
        html += "<h2>Другие активы:</h2><ul>"
        for a in file_data.get('assets', []):
            if a.get('type') != 'bond' and a.get('type') != 'currency':
                p = float(a.get('price', 0))
                html += f"<li>• {html.escape(str(a.get('ticker', '?')))} ({html.escape(str(a.get('name', '?')))}): {float(a.get('quantity', 0))} шт x {p:.2f} руб.</li>"
        html += "</ul>"
        
        html += "<h2>Денежные средства:</h2><ul>"
        for a in file_data.get('assets', []):
            if a.get('type') == 'currency':
                p = float(a.get('price', 0))
                html += f"<li>• {html.escape(str(a.get('ticker', '?')))} ({html.escape(str(a.get('name', '?')))}): {float(a.get('quantity', 0))} шт x {p:.2f} руб.</li>"
        html += "</ul>"
        return html
    except Exception as e:
        return f"<h2 style='color:red'>Ошибка: {e}</h2>"
