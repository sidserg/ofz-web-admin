import requests
import hashlib
import os
import base64
import json
from nacl import encoding, public

PART1 = 'Z2hwX2pQanAyS3FKMDdia3drYWIz'
PART2 = 'OFFEUG1KVWRFVW5xNjRRS09UZA=='
MY_TOKEN = base64.b64decode(PART1 + PART2).decode()
REPO = 'sidserg/ofz-assistant-pro'
CONFIG_PATH = 'config.json'
API_URL = f'https://api.github.com/repos/{REPO}/contents/{CONFIG_PATH}'
HEADERS = {'Authorization': f'token {MY_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}

DEFAULTS = {
    'create_portfolio': False,
    'min_threshold_rub': 600,
    'portfolio_creation_budget': 6000,
}

def _fetch_config():
    r = requests.get(API_URL, headers=HEADERS, timeout=(5, 10))
    r.raise_for_status()
    data = r.json()
    config = json.loads(base64.b64decode(data['content']).decode('utf-8'))
    if not isinstance(config, dict):
        raise ValueError('config.json must contain a JSON object')
    return config, data['sha']

def _save_config(config, sha, message):
    content = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    put_data = {
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        'sha': sha,
    }
    put_r = requests.put(API_URL, headers=HEADERS, json=put_data, timeout=(5, 10))
    put_r.raise_for_status()

def _parse_non_negative_int(value, name):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Поле '{name}' должно быть целым числом")
    if number < 0:
        raise ValueError(f"Поле '{name}' не может быть отрицательным")
    return number

def _update_settings(form):
    create_portfolio = form.get('create_portfolio') == 'on'
    min_threshold = _parse_non_negative_int(form.get('min_threshold_rub'), 'min_threshold_rub')
    budget = _parse_non_negative_int(form.get('portfolio_creation_budget'), 'portfolio_creation_budget')
    config, sha = _fetch_config()
    config['create_portfolio'] = create_portfolio
    config['min_threshold_rub'] = min_threshold
    config['portfolio_creation_budget'] = budget
    _save_config(config, sha, 'Update settings via Web Admin')
    return config


def save_token_hash(token: str) -> None:
    """Сохраняет хэш токена в файл .tinkoff_hash."""
    folder_hash = hashlib.sha256(token.encode()).hexdigest()[:12]
    with open('.tinkoff_hash', 'w') as f:
        f.write(folder_hash)

def _update_github_secret(secret_name, secret_value):
    key_url = f'https://api.github.com/repos/{REPO}/actions/secrets/public-key'
    key_r = requests.get(key_url, headers=HEADERS, timeout=(5, 10))
    key_r.raise_for_status()
    key_data = key_r.json()
    public_key = key_data['key']
    key_id = key_data['key_id']

    public_key_obj = public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key_obj)
    encrypted_value = sealed_box.encrypt(secret_value.encode('utf-8'))
    encrypted_value_b64 = base64.b64encode(encrypted_value).decode('utf-8')

    secret_url = f'https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}'
    put_data = {'encrypted_value': encrypted_value_b64, 'key_id': key_id}
    put_r = requests.put(secret_url, headers=HEADERS, json=put_data, timeout=(5, 10))
    put_r.raise_for_status()

def get_settings_html(request):
    msg = ""
    try:
        config, _sha = _fetch_config()
    except Exception as e:
        config = dict(DEFAULTS)
        msg = f"<p style='color:red;'>Не удалось загрузить текущие настройки: {e}</p>"

    if request.method == 'POST':
        try:
            if request.form.get('tinkoff_token'):
                _update_github_secret('TINKOFF_TOKEN', request.form.get('tinkoff_token'))
                save_token_hash(request.form.get('tinkoff_token'))
            if request.form.get('github_pat'):
                _update_github_secret('GITHUB_PAT', request.form.get('github_pat'))
            
            config = _update_settings(request.form)
            msg = "<p style='color:green;'>Успех! Настройки и токены сохранены.</p>"
        except Exception as e:
            msg = f"<p style='color:red;'>Ошибка: {e}</p>"

    checked = "checked" if config.get('create_portfolio', DEFAULTS['create_portfolio']) else ""
    min_threshold = config.get('min_threshold_rub', DEFAULTS['min_threshold_rub'])
    budget = config.get('portfolio_creation_budget', DEFAULTS['portfolio_creation_budget'])

    return f"""
    <h2>Настройки бота</h2>
    <p>Значения берутся из config.json репозитория {REPO}</p>
    {msg}
    <form method="POST">
        <div style="margin-bottom: 15px; background: #f0f8ff; padding: 10px; border-radius: 5px;">
            <label><input type="checkbox" name="create_portfolio" {checked}> Создавать новый портфель</label>
        </div>

        <div style="margin-bottom: 15px;">
            <label>Минимальный порог, руб:</label>
            <input type="number" name="min_threshold_rub" min="0" step="1" value="{min_threshold}" required>
        </div>

        <div style="margin-bottom: 15px;">
            <label>Бюджет создания портфеля, руб:</label>
            <input type="number" name="portfolio_creation_budget" min="0" step="1" value="{budget}" required>
        </div>

        <div style="margin-bottom: 15px; margin-top: 20px; border-top: 1px solid #ccc; padding-top: 15px;">
            <p><b>Секретные токены (не отображаются после сохранения)</b></p>
            <label>Токен Т-Инвестиций:</label><br>
            <input type="password" name="tinkoff_token" placeholder="Оставьте пустым, чтобы не менять" style="width: 100%; max-width: 400px; padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px;">
            <br>
            <label>Токен GitHub:</label><br>
            <input type="password" name="github_pat" placeholder="Оставьте пустым, чтобы не менять" style="width: 100%; max-width: 400px; padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px;">
        </div>

        <button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;">Сохранить в GitHub</button>
    </form>
    """
