import base64
import calendar
import html
from datetime import date, datetime

import requests

PART1 = 'Z2hwX2pQanAyS3FKMDdia3drYWIz'
PART2 = 'OFFEUG1KVWRFVW5xNjRRS09UZA=='
MY_TOKEN = base64.b64decode(PART1 + PART2).decode()
REPO = 'sidserg/ofz-assistant-pro'
API_URL = f'https://api.github.com/repos/{REPO}/contents/reports'
HEADERS = {'Authorization': f'token {MY_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}

WEEKDAYS = ('Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс')
MONTHS = ('Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
          'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь')


def _to_float(value):
    """Converts a value from report JSON to float; returns 0.0 for None/garbage."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fetch_reports_by_day():
    """Lists reports/ and returns {YYYY-MM-DD: {'name': ..., 'download_url': ...}} (latest file per day)."""
    r = requests.get(API_URL, headers=HEADERS, timeout=(5, 10))
    r.raise_for_status()
    items = r.json()
    by_day = {}
    if not isinstance(items, list):
        return by_day
    for item in items:
        name = item.get('name', '')
        if item.get('type') != 'file' or not name.endswith('.json'):
            continue
        day = name[:10]
        try:
            datetime.strptime(day, '%Y-%m-%d')
        except ValueError:
            continue
        # File names start with a sortable timestamp, so the lexicographically
        # greatest name of a day is its latest report.
        if day not in by_day or name > by_day[day]['name']:
            by_day[day] = {'name': name, 'download_url': item.get('download_url')}
    return by_day


def _fetch_report_details(download_url):
    """Downloads one report JSON. Returns dict or None."""
    if not download_url:
        return None
    r = requests.get(download_url, timeout=(5, 10))
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, dict) else None


def _render_details(day, report):
    """Renders the details block for one day."""
    if report is None:
        return "<p style='color:red;'>Не удалось загрузить файл отчёта.</p>"

    esc = lambda v: html.escape(str(v if v is not None else '—'), quote=True)
    html_out = "<h2>Отчёт за {0}</h2>".format(esc(day))
    html_out += "<p><b>Дата:</b> {0}</p>".format(esc(report.get('date', '—')))
    html_out += "<p><b>Портфель:</b> {0}</p>".format(esc(report.get('portfolio', '—')))
    html_out += "<p><b>Баланс:</b> {0:.2f} руб.</p>".format(_to_float(report.get('free_rub')))
    html_out += "<p><b>Статус:</b> {0}</p>".format(esc(report.get('status', '—')))
    html_out += "<p><b>Действие:</b> {0}</p>".format(esc(report.get('action', '—')))

    assets = report.get('assets')
    bonds = [a for a in assets if isinstance(a, dict) and a.get('type') == 'bond'] if isinstance(assets, list) else []
    html_out += "<h2>Облигации</h2>"
    if not bonds:
        html_out += "<p>Нет облигаций в отчёте.</p>"
    else:
        html_out += "<ul>"
        for a in bonds:
            html_out += "<li>• {0} ({1}): {2} шт x {3:.2f} руб.</li>".format(
                esc(a.get('ticker', '?')), esc(a.get('name', '?')),
                _to_float(a.get('quantity')), _to_float(a.get('price')))
        html_out += "</ul>"
    html_out += "<p><a href='/calendar'>&larr; Назад к календарю</a></p>"
    return html_out


def _render_calendar(by_day, today):
    """Renders the month grid; days with reports are green links, others are plain cells."""
    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(today.year, today.month)

    html_out = "<h2>Календарь: {0} {1}</h2>".format(MONTHS[today.month - 1], today.year)
    html_out += (
        "<table style='border-collapse: collapse; width: 100%; max-width: 560px; table-layout: fixed;'>"
        "<tr>"
    )
    for wd in WEEKDAYS:
        html_out += "<th style='border: 1px solid #ccc; padding: 6px; background: #f0f0f0;'>{0}</th>".format(wd)
    html_out += "</tr>"
    for week in weeks:
        html_out += "<tr>"
        for day_num in week:
            if day_num == 0:
                html_out += "<td style='border: 1px solid #ccc; height: 44px;'>&nbsp;</td>"
                continue
            day_str = "{0:04d}-{1:02d}-{2:02d}".format(today.year, today.month, day_num)
            report = by_day.get(day_str)
            style = "border: 1px solid #ccc; text-align: center; vertical-align: middle; height: 44px;"
            if day_num == today.day:
                style += " font-weight: bold; outline: 2px solid #2980b9; outline-offset: -2px;"
            if report:
                html_out += (
                    "<td style='{0} background: #d4edda;'>".format(style)
                    + "<a href='/calendar?day={0}' title='{1}' style='color: #155724; text-decoration: none;'>".format(day_str, html.escape(report["name"], quote=True))
                    + "&#10003; {0}".format(day_num)
                    + "</a></td>"
                )
            else:
                html_out += "<td style='{0}'>{1}</td>".format(style, day_num)
        html_out += "</tr>"
    html_out += "</table>"
    html_out += "<p style='color:#777; font-size: 13px;'>Зелёным отмечены дни, за которые есть отчёт. Нажмите на день, чтобы посмотреть детали.</p>"
    return html_out


def get_calendar_html(request):
    today = date.today()
    msg = ""
    by_day = {}
    try:
        by_day = _fetch_reports_by_day()
    except Exception as e:
        msg = f"<p style='color:red;'>Не удалось получить список отчётов: {e}</p>"

    day = request.args.get('day', '')
    if day:
        # Reject anything that is not a plain YYYY-MM-DD string before using it
        try:
            datetime.strptime(day, '%Y-%m-%d')
        except ValueError:
            day = ''
    if day:
        if day not in by_day:
            content = f"<p style='color:red;'>Отчёта за {html.escape(day, quote=True)} нет.</p>"
        else:
            try:
                report = _fetch_report_details(by_day[day]['download_url'])
                content = _render_details(day, report)
            except Exception as e:
                content = f"<p style='color:red;'>Ошибка загрузки отчёта: {e}</p>"
    else:
        content = _render_calendar(by_day, today)

    return msg + content