import html
import os

import requests

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
REPO = 'sidserg/ofz-assistant-pro'


def get_token_hash() -> str:
    from flask import request
    return request.cookies.get("tinkoff_hash", "")


def _to_float(value) -> float:
    """Возвращает float, не падая на None/строке/битом значении."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def get_status_html():
    token_hash = get_token_hash()
    if not token_hash:
        return "<h2 style='color: #e74c3c;'>Введите токен Т-Инвестиций в настройках, чтобы увидеть отчеты.</h2>"
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
        r = requests.get(f'https://api.github.com/repos/{REPO}/contents/reports/{token_hash}', headers=headers, timeout=(5, 10))
        if r.status_code == 404:
            return "<div style='padding: 20px; background: #fef9e7; border-left: 5px solid #f39c12;'><h3 style='color: #f39c12; margin-top: 0;'>⏳ Ожидание первого отчета</h3><p>Токен успешно сохранён. Бот ещё не запускался с новым токеном.</p><p>Вы можете подождать, пока бот сработает по расписанию, или нажать кнопку <b>«Запуск»</b> в левом меню, чтобы запустить его вручную.</p></div>"
        if r.status_code != 200:
            # 401/403/422 приходят JSON-объектом, а не списком файлов.
            return f"<h2 style='color:red'>GitHub API вернул {r.status_code} для папки reports/{html.escape(token_hash)}</h2>"
        files = r.json()
        if not isinstance(files, list):
            return "<h2>Отчетов пока нет.</h2>"
        if not files:
            return "<h2>Отчетов пока нет.</h2>"

        latest = max(files, key=lambda x: str(x.get("name", "")))
        download_url = latest.get("download_url")
        if not download_url:
            return "<h2 style='color:red'>У последнего отчета нет download_url.</h2>"
        file_resp = requests.get(download_url, timeout=(5, 10))
        file_resp.raise_for_status()
        file_data = file_resp.json()
        if not isinstance(file_data, dict):
            return "<h2 style='color:red'>Некорректный формат файла отчета.</h2>"
        
        # Форматируем дату
        raw_date = str(file_data.get('date', '—'))
        try:
            dt = raw_date.split('.')[0]
            parts = dt.split(' ')
            date_part = parts[0]
            time_part = parts[1][:5]
            y, m, d = date_part.split('-')
            formatted_date = f"{d}-{m}-{y}"
            formatted_time = time_part
        except Exception:
            formatted_date = raw_date
            formatted_time = ""

        html_str = "<h2>Последний результат отработки</h2>"
        html_str += f"<p><b>Дата:</b> <span style='color: red; font-weight: bold;'>{html.escape(formatted_time)}</span>    {html.escape(formatted_date)}</p>"
        html_str += f"<p><b>Портфель:</b> {html.escape(str(file_data.get('portfolio', '—')))}</p>"
        html_str += f"<p><b>Баланс:</b> {_to_float(file_data.get('free_rub', 0)):.2f} руб.</p>"
        html_str += f"<p><b>Статус:</b> {html.escape(str(file_data.get('status', '—')))}</p>"
        html_str += f"<p><b>Действие:</b> {html.escape(str(file_data.get('action', '—')))}</p>"
        
        html_str += "<h2>Облигации:</h2><ul>"
        for a in file_data.get('assets', []):
            if a.get('type') == 'bond':
                p = _to_float(a.get('price', 0))
                html_str += f"<li>• {html.escape(str(a.get('ticker', '?')))} ({html.escape(str(a.get('name', '?')))}): {_to_float(a.get('quantity', 0))} шт x {p:.2f} руб.</li>"
        html_str += "</ul>"
        
        html_str += "<h2>Другие активы:</h2><ul>"
        for a in file_data.get('assets', []):
            if a.get('type') != 'bond' and a.get('type') != 'currency':
                p = _to_float(a.get('price', 0))
                html_str += f"<li>• {html.escape(str(a.get('ticker', '?')))} ({html.escape(str(a.get('name', '?')))}): {_to_float(a.get('quantity', 0))} шт x {p:.2f} руб.</li>"
        html_str += "</ul>"
        
        html_str += "<h2>Денежные средства:</h2><ul>"
        for a in file_data.get('assets', []):
            if a.get('type') == 'currency':
                p = _to_float(a.get('price', 0))
                html_str += f"<li>• {html.escape(str(a.get('ticker', '?')))} ({html.escape(str(a.get('name', '?')))}): {_to_float(a.get('quantity', 0))} шт x {p:.2f} руб.</li>"
        html_str += "</ul>"
        
        return html_str
    except Exception as e:
        return f"<h2 style='color:red'>Ошибка: {html.escape(str(e))}</h2>"
