"""Модуль календаря на весь год для Flask-веб-интерфейса."""
import calendar as cal_module
import base64
import requests
from datetime import date
import html

MONTH_NAMES = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
WEEK_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

GITHUB_REPO = "sidserg/ofz-assistant-pro"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"

def get_token_hash() -> str:
    """Читает хэш токена из файла .tinkoff_hash."""
    try:
        with open('.tinkoff_hash', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return ''

def _get_github_files(pat: str, path: str) -> list[dict]:
    if not pat or path == "reports/" or path == "reports":
        return []
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"{GITHUB_API_URL}/contents/{path}"
    try:
        resp = requests.get(url, headers=headers, timeout=(5, 10))
        if resp.status_code != 200:
            return []
        return resp.json()
    except requests.RequestException:
        return []

def _get_report_dates(pat: str, year: int) -> set:
    dates = set()
    files = _get_github_files(pat, f"reports/{get_token_hash()}")
    for f in files:
        name = f.get("name", "")
        if len(name) >= 10 and name[:4] == str(year):
            date_str = name[:10]
            try:
                date.fromisoformat(date_str)
                dates.add(date_str)
            except ValueError:
                pass
    return dates

def _load_report_from_github(pat: str, date_str: str) -> dict | None:
    files = _get_github_files(pat, f"reports/{get_token_hash()}")
    for f in files:
        name = f.get("name", "")
        if name.startswith(date_str + "_"):
            download_url = f.get("download_url")
            if download_url:
                try:
                    resp = requests.get(download_url, timeout=(5, 10))
                    if resp.status_code == 200:
                        return resp.json()
                except requests.RequestException:
                    pass
    return None

def _render_month(year: int, month: int, report_dates: set) -> str:
    first_weekday, days_in_month = cal_module.monthrange(year, month)
    offset = first_weekday

    html_out = '<div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-bottom: 10px; background: white;">'
    html_out += f'<div style="text-align: center; font-weight: bold; margin-bottom: 5px; color: #2c3e50;">{MONTH_NAMES[month - 1]}</div>'
    html_out += '<table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 14px;">'
    html_out += '<tr style="color: #7f8c8d; font-size: 12px;">'
    for wd in WEEK_DAYS:
        html_out += f"<th style='padding: 2px;'>{wd}</th>"
    html_out += "</tr><tr>"

    cell = 0
    for _ in range(offset):
        html_out += "<td></td>"
        cell += 1

    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        if date_str in report_dates:
            html_out += f'<td style="padding: 2px;"><a href="/calendar?day={date_str}" style="color: white; background: #27ae60; display: block; text-decoration: none; border-radius: 3px;">{day}</a></td>'
        else:
            html_out += f'<td style="padding: 2px; color: #000;">{day}</td>'
        cell += 1
        if cell % 7 == 0 and day != days_in_month:
            html_out += "</tr><tr>"

    while cell % 7 != 0:
        html_out += "<td></td>"
        cell += 1

    html_out += "</tr></table></div>"
    return html_out

def _render_report_detail(date_str: str, pat: str) -> str:
    data = _load_report_from_github(pat, date_str)
    if data is None:
        return f"<div style='color:red;'>Отчёт за {html.escape(date_str)} не найден.</div>"

    bonds = [a for a in data.get("assets", []) if a.get("type") == "bond"]

    html_out = f'<div style="background: #f4f6f9; padding: 15px; border-radius: 5px; margin-bottom: 20px;">'
    html_out += f'<a href="/calendar" style="color: #3498db; text-decoration: none;">&larr; Назад к календарю</a>'
    html_out += f"<h2 style='margin-top: 10px;'>Отчёт за {html.escape(date_str)}</h2>"
    html_out += f"<p><b>Портфель:</b> {html.escape(str(data.get('portfolio', '—')))}</p>"
    html_out += f"<p><b>Баланс:</b> {float(data.get('free_rub', 0)):.2f} руб.</p>"
    html_out += f"<p><b>Статус:</b> {html.escape(str(data.get('status', '—')))}</p>"
    html_out += "<h3>Облигации</h3><ul style='list-style: none; padding: 0;'>"
    for b in bonds:
        price = float(b.get('price', 0))
        html_out += f"<li style='padding: 2px 0;'>{html.escape(str(b.get('ticker')))} ({html.escape(str(b.get('name')))}): {float(b.get('quantity', 0))} шт x {price:.2f} руб.</li>"
    if not bonds:
        html_out += "<li>Нет облигаций</li>"
    html_out += "</ul></div>"
    return html_out

def _render_year_nav(year: int) -> str:
    return f'''
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: white; padding: 10px; border-radius: 5px;">
        <a href="/calendar?year={year - 1}" style="text-decoration: none; color: #3498db; font-weight: bold;">&laquo; {year - 1}</a>
        <span style="font-size: 20px; font-weight: bold; color: #2c3e50;">{year}</span>
        <a href="/calendar?year={year + 1}" style="text-decoration: none; color: #3498db; font-weight: bold;">{year + 1} &raquo;</a>
    </div>
    '''



def get_calendar_html(request, pat: str) -> str:
    year_str = request.args.get("year", "")
    day_str = request.args.get("day", "")

    if year_str.isdigit():
        year = int(year_str)
    elif day_str and len(day_str) >= 4 and day_str[:4].isdigit():
        year = int(day_str[:4])
    else:
        year = date.today().year

    report_dates = _get_report_dates(pat, year)

    html_out = "<h2>Календарь отчётов</h2>"
    html_out += _render_year_nav(year)

    if day_str:
        # Если выбран день, показываем ТОЛЬКО детали отчета
        html_out += _render_report_detail(day_str, pat)
    else:
        # Если день не выбран, показываем сетку календаря
        html_out += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px;">'
        for month in range(1, 13):
            html_out += _render_month(year, month, report_dates)
        html_out += "</div>"

    return html_out
