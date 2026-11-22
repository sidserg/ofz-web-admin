from flask import request, redirect, url_for, render_template_string
import json, os, hashlib, requests

DEFAULTS = {"min_threshold": 600, "portfolio_budget": 6000, "create_new_portfolio": False}

def _fetch_config():
    # Заглушка для теста (чтобы не дергать GitHub при загрузке страницы)
    return DEFAULTS, "test_sha"

def _update_settings(form):
    # Заглушка
    return DEFAULTS

def _update_github_secret(name, value):
    # Заглушка (не обращаемся к GitHub)
    print(f"Тестовое сохранение секрета {name}")

def save_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:12]

def get_settings_html(request):
    msg = ""
    config = dict(DEFAULTS)

    if request.method == 'POST':
        try:
            tinkoff_token = request.form.get('tinkoff_token')
            if tinkoff_token:
                folder_hash = save_token_hash(tinkoff_token)
                resp = redirect(url_for('settings_page'))
                resp.set_cookie('tinkoff_hash', folder_hash, max_age=86400*30, httponly=True, samesite='Lax')
                return resp
            
            msg = "<p style='color:green;'>Успех! Настройки сохранены (тестовый режим).</p>"
        except Exception as e:
            import traceback
            traceback.print_exc()
            msg = f"<p style='color:red;'>Ошибка: {e}</p>"

    return f"""
    <h2>Настройки бота (ТЕСТ)</h2>
    {msg}
    <form method="post">
        <label>Токен Т-Инвестиций:</label><br>
        <input type="password" name="tinkoff_token" placeholder="Введите токен"><br><br>
        <button type="submit">Сохранить</button>
    </form>
    """
