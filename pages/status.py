import requests
import base64
import html

PART1 = 'Z2hwX2pQanAyS3FKMDdia3drYWIz'
PART2 = 'OFFEUG1KVWRFVW5xNjRRS09UZA=='
MY_TOKEN = base64.b64decode(PART1 + PART2).decode()
REPO = 'sidserg/ofz-assistant-pro'


def get_token_hash() -> str:
    """Читает хэш токена из файла .tinkoff_hash."""
    try:
        with open('.tinkoff_hash', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return ''

def get_status_html():
    token_hash = get_token_hash()
    if not token_hash:
        return "<h2 style='color: #e74c3c;'>Введите токен Т-Инвестиций в настройках, чтобы увидеть отчеты.</h2>"
    try:
        headers = {'Authorization': f'token {MY_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
        r = requests.get(f'https://api.github.com/repos/{REPO}/contents/reports/{token_hash}', headers=headers, timeout=(5, 10))
        if r.status_code == 404:
            return "<div style='padding: 20px; background: #fef9e7; border-left: 5px solid #f39c12;'><h3 style='color: #f39c12; margin-top: 0;'>⏳ Ожидание первого отчета</h3><p>Токен успешно сохранён. Бот ещё не запускался с новым токеном.</p><p>Вы можете подождать, пока бот сработает по расписанию, или нажать кнопку <b>«Запуск»</b> в левом меню, чтобы запустить его вручную.</p></div>"
        files = r.json()
        if not files:
            return "<h2>Отчетов пока нет.</h2>"
        
        latest = sorted(files, key=lambda x: x["name"], reverse=True)[0]
        file_data = requests.get(latest["download_url"], timeout=(5, 10)).json()
        
        # Форматируем дату
        raw_date = str(file_data.get('date', '—'))
        try:
            dt = raw_date.split('.')[0]
            parts = dt.split(' ')
            date_part = parts[0]
            time_part = parts[1][:5]
            y, m, d = date_part.split('-')
            formatted_date = f"{time_part}    {d}-{m}-{y}"
        except Exception:
            formatted_date = raw_date

        html_str = f"<h2>Последний результат отработки</h2>"
        html_str += f"<p><b>Дата:</b> {html.escape(formatted_date)}</p>"
        html_str += f"<p><b>Портфель:</b> {html.escape(str(file_data.get('portfolio', '—')))}</p>"
        html_str += f"<p><b>Баланс:</b> {float(file_data.get('free_rub', 0)):.2f} руб.</p>"
        html_str += f"<p><b>Статус:</b> {html.escape(str(file_data.get('status', '—')))}</p>"
        html_str += f"<p><b>Действие:</b> {html.escape(str(file_data.get('action', '—')))}</p>"
        
        html_str += "<h2>Облигации:</h2><ul>"
        for a in file_data.get('assets', []):
            if a.get('type') == 'bond':
                p = float(a.get('price', 0))
                html_str += f"<li>• {html.escape(str(a.get('ticker', '?')))} ({html.escape(str(a.get('name', '?')))}): {float(a.get('quantity', 0))} шт x {p:.2f} руб.</li>"
        html_str += "</ul>"
        
        html_str += "<h2>Другие активы:</h2><ul>"
        for a in file_data.get('assets', []):
            if a.get('type') != 'bond' and a.get('type') != 'currency':
                p = float(a.get('price', 0))
                html_str += f"<li>• {html.escape(str(a.get('ticker', '?')))} ({html.escape(str(a.get('name', '?')))}): {float(a.get('quantity', 0))} шт x {p:.2f} руб.</li>"
        html_str += "</ul>"
        
        html_str += "<h2>Денежные средства:</h2><ul>"
        for a in file_data.get('assets', []):
            if a.get('type') == 'currency':
                p = float(a.get('price', 0))
                html_str += f"<li>• {html.escape(str(a.get('ticker', '?')))} ({html.escape(str(a.get('name', '?')))}): {float(a.get('quantity', 0))} шт x {p:.2f} руб.</li>"
        html_str += "</ul>"
        
        return html_str
    except Exception as e:
        return f"<h2 style='color:red'>Ошибка: {e}</h2>"
