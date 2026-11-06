import requests
import base64
import re

PART1 = 'Z2hwX2pQanAyS3FKMDdia3drYWIz'
PART2 = 'OFFEUG1KVWRFVW5xNjRRS09UZA=='
MY_TOKEN = base64.b64decode(PART1 + PART2).decode()
REPO = 'sidserg/ofz-assistant-pro'

def get_schedule_html(request):
    msg = ""
    current_cron = "0 17 * * *"
    h_msk, m = 20, 0
    
    try:
        headers = {'Authorization': f'token {MY_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
        url = f'https://api.github.com/repos/{REPO}/contents/.github/workflows/bot.yml'
        r = requests.get(url, headers=headers, timeout=(5, 10))
        r.raise_for_status()
        data = r.json()
        yml = base64.b64decode(data['content']).decode('utf-8')
        sha = data['sha']
        
        match = re.search(r"cron: '(.*?)'", yml)
        if match:
            current_cron = match.group(1)
            
    except Exception as e:
        msg = f"<p style='color:red;'>Не удалось загрузить текущее расписание: {e}</p>"
        return msg

    parts = current_cron.split()
    if len(parts) >= 2:
        try:
            m = int(parts[0])
            h_utc = int(parts[1])
            h_msk = (h_utc + 3) % 24
        except:
            pass

    if request.method == 'POST':
        try:
            mode = request.form.get('selected_mode', 'daily')
            if mode == 'minute':
                interval = int(request.form['interval_minutes'])
                if not (1 <= interval <= 59):
                    raise ValueError("Интервал минут должен быть от 1 до 59")
                cron = f"*/{interval} * * * *"
                msg_text = f"каждые {interval} минут"
            elif mode == 'daily':
                h = int(request.form['hour'])
                m = int(request.form['minute'])
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError("Неверное время")
                h_utc = (h - 3) % 24
                cron = f"{m} {h_utc} * * *"
                msg_text = f"ежедневно в {h:02d}:{m:02d} МСК"
            elif mode == 'monthly':
                month_interval = int(request.form['interval_months'])
                h = int(request.form['hour_m'])
                m = int(request.form['minute_m'])
                if not (1 <= month_interval <= 12 and 0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError("Неверные параметры месяца")
                h_utc = (h - 3) % 24
                cron = f"{m} {h_utc} */{month_interval} * *"
                msg_text = f"каждые {month_interval} месяцев в {h:02d}:{m:02d} МСК"
            else:
                raise ValueError('Неизвестный режим')

            new_yml = re.sub(r"cron: '.*?'", f"cron: '{cron}'", yml)
            if new_yml == yml and cron not in yml:
                 raise ValueError("Не удалось найти строку с cron в файле")
                 
            put_data = {
                'message': f'Update schedule: {msg_text} (Web)',
                'content': base64.b64encode(new_yml.encode('utf-8')).decode('utf-8'),
                'sha': sha
            }
            put_r = requests.put(url, headers=headers, json=put_data, timeout=(5, 10))
            put_r.raise_for_status()
            msg = f"<p style='color:green;'>Успех! Бот будет запускаться {msg_text}.</p>"
            h_msk = h
            m = m
        except Exception as e:
            msg = f"<p style='color:red;'>Ошибка: {e}</p>"

    return f"""
    <h2>График выполнения</h2>
    <p>Время указывается по Москве (МСК)</p>
    {msg}
    <form method="POST">
        <input type="hidden" name="selected_mode" id="selected_mode" value="daily">
        
        <div style="margin-bottom: 15px;">
            <label><input type="radio" name="type" value="minute" onchange="document.getElementById('selected_mode').value=this.value"> Каждые 
            <input type="number" name="interval_minutes" value="15"> минут(ы)</label>
        </div>
        
        <div style="margin-bottom: 15px; background: #f0f8ff; padding: 10px; border-radius: 5px;">
            <label><input type="radio" name="type" value="daily" checked onchange="document.getElementById('selected_mode').value=this.value"> Каждый день в</label>
            <input type="number" name="hour" min="0" max="23" value="{h_msk}" required> :
            <input type="number" name="minute" min="0" max="59" value="{m}" required>
        </div>
        
        <div style="margin-bottom: 15px;">
            <label><input type="radio" name="type" value="monthly" onchange="document.getElementById('selected_mode').value=this.value"> Каждые 
            <input type="number" name="interval_months" value="1"> месяца в</label>
            <input type="number" name="hour_m" value="19"> :
            <input type="number" name="minute_m" value="0">
        </div>
        
        <button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;">Сохранить</button>
    </form>
    """
