import requests
import base64
import json

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
    """Reads config.json from GitHub. Returns (config: dict, sha: str)."""
    r = requests.get(API_URL, headers=HEADERS, timeout=(5, 10))
    r.raise_for_status()
    data = r.json()
    config = json.loads(base64.b64decode(data['content']).decode('utf-8'))
    if not isinstance(config, dict):
        raise ValueError('config.json must contain a JSON object')
    return config, data['sha']


def _save_config(config, sha, message):
    """Saves config.json to GitHub via the Contents API."""
    content = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    put_data = {
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        'sha': sha,
    }
    put_r = requests.put(API_URL, headers=HEADERS, json=put_data, timeout=(5, 10))
    put_r.raise_for_status()


def _parse_non_negative_int(value, name):
    """Validates that the value is a non-negative integer."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Field '{name}' must be an integer")
    if number < 0:
        raise ValueError(f"Field '{name}' cannot be negative")
    return number


def _update_settings(form):
    """Validates the form, re-reads the file (fresh sha) and saves. Returns the new config."""
    create_portfolio = form.get('create_portfolio') == 'on'
    min_threshold = _parse_non_negative_int(form.get('min_threshold_rub'), 'min_threshold_rub')
    budget = _parse_non_negative_int(form.get('portfolio_creation_budget'), 'portfolio_creation_budget')

    # Re-read the file: fresh sha (avoids 409) and unknown keys (e.g. 'schedule') are preserved
    config, sha = _fetch_config()
    config['create_portfolio'] = create_portfolio
    config['min_threshold_rub'] = min_threshold
    config['portfolio_creation_budget'] = budget
    _save_config(config, sha, 'Update settings via Web Admin')
    return config


def get_settings_html(request):
    msg = ""
    try:
        config, _sha = _fetch_config()
    except Exception as e:
        config = dict(DEFAULTS)
        msg = f"<p style='color:red;'>Не удалось загрузить текущие настройки: {e}. Показаны значения по умолчанию.</p>"

    if request.method == 'POST':
        try:
            config = _update_settings(request.form)
            msg = "<p style='color:green;'>Успех! Настройки сохранены в config.json.</p>"
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
            <label><input type="checkbox" name="create_portfolio" {checked}> Создавать новый портфель (create_portfolio)</label>
        </div>

        <div style="margin-bottom: 15px;">
            <label>Минимальный порог, руб (min_threshold_rub):</label>
            <input type="number" name="min_threshold_rub" min="0" step="1" value="{min_threshold}" required>
        </div>

        <div style="margin-bottom: 15px;">
            <label>Бюджет создания портфеля, руб (portfolio_creation_budget):</label>
            <input type="number" name="portfolio_creation_budget" min="0" step="1" value="{budget}" required>
        </div>

        <button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;">Сохранить в GitHub</button>
    </form>
    """