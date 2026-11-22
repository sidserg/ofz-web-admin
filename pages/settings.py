import base64
import hashlib
import html
import json
import os
import traceback

import requests
from flask import flash, redirect, url_for
from nacl import encoding, public

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
REPO = 'sidserg/ofz-assistant-pro'
CONFIG_PATH = 'config.json'
API_URL = f'https://api.github.com/repos/{REPO}/contents/{CONFIG_PATH}'
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}

DEFAULTS = {
    'create_portfolio': False,
    'min_threshold_rub': 600,
    'portfolio_creation_budget': 6000,
}

def _fetch_config():
    r = requests.get(API_URL, headers=HEADERS, timeout=(5, 10))
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict) or 'content' not in data or 'sha' not in data:
        raise ValueError('GitHub API вернул неожиданную структуру для config.json')
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

def _update_settings(form, config, sha):
    """Применяет поля формы к config и сохраняет его в GitHub.

    Args:
        form: Flask request.form с полями настроек.
        config: конфигурация из _fetch_config().
        sha: commit-sha config.json из того же ответа.

    Returns:
        dict: обновлённая конфигурация.

    Raises:
        ValueError: если числовые поля невалидны (до любой записи).
    """
    create_portfolio = form.get('create_portfolio') == 'on'
    min_threshold = _parse_non_negative_int(form.get('min_threshold_rub'), 'min_threshold_rub')
    budget = _parse_non_negative_int(form.get('portfolio_creation_budget'), 'portfolio_creation_budget')
    config['create_portfolio'] = create_portfolio
    config['min_threshold_rub'] = min_threshold
    config['portfolio_creation_budget'] = budget
    _save_config(config, sha, 'Update settings via Web Admin [skip ci]')
    return config


def save_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:12]


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
    config = dict(DEFAULTS)  # fallback по умолчанию
    sha = None               # None означает, что config.json не загрузили
    try:
        config, sha = _fetch_config()
    except Exception as e:
        traceback.print_exc()
        msg = f"<p style='color:red;'>Не удалось загрузить текущие настройки: {html.escape(str(e))}</p>"

    if request.method == 'POST':
        tinkoff_token = request.form.get('tinkoff_token')
        try:
            # 1. Сначала обычные настройки: _update_settings валидирует поля
            #    до любой записи, поэтому невалидная форма не тронет секреты.
            if sha is None:
                config, sha = _fetch_config()
            config = _update_settings(request.form, config, sha)

            # 2. Обновляем секретные токены, если они введены
            folder_hash = ""
            if tinkoff_token:
                _update_github_secret('TINKOFF_TOKEN', tinkoff_token)
                folder_hash = save_token_hash(tinkoff_token)

            if request.form.get('github_pat'):
                _update_github_secret('GITHUB_PAT', request.form.get('github_pat'))

        except Exception as e:
            traceback.print_exc()
            # Остались на форме без redirect: пользователь видит, что исправить.
            msg = f"<p style='color:red;'>Ошибка при сохранении: {html.escape(str(e))}</p>"
        else:
            # Успех уходит через flash + redirect (PRG), иначе сообщение
            # перезаписывалось бы следующим GET-запросом.
            flash('Настройки и токены сохранены.', 'success')
            resp = redirect(url_for('settings_page'))
            if folder_hash:
                resp.set_cookie(
                    'tinkoff_hash',
                    folder_hash,
                    max_age=86400 * 30,
                    httponly=True,
                    samesite='Lax',
                    # request.is_secure — property (Werkzeug >= 2.1).
                    # На Amvera с ProxyFix даст True, на http://localhost — False.
                    secure=request.is_secure,
                )
            return resp

    checked = "checked" if config.get('create_portfolio', DEFAULTS['create_portfolio']) else ""
    min_threshold = html.escape(str(config.get('min_threshold_rub', DEFAULTS['min_threshold_rub'])))
    budget = html.escape(str(config.get('portfolio_creation_budget', DEFAULTS['portfolio_creation_budget'])))

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
