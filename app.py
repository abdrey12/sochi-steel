import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Ограничение размера запроса: 12 МБ (форма + фото)
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024

# ---------- НАСТРОЙКИ ----------
SMTP_SERVER = "smtp.mail.ru"
SMTP_PORT = 465          # SSL
SMTP_TIMEOUT = 10        # критично: без таймаута запрос висит до минуты

SENDER_EMAIL = os.getenv("SMTP_EMAIL", "o.p.f.1994@mail.ru")
TARGET_EMAIL = os.getenv("SMTP_TARGET", "o.p.f.1994@mail.ru")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

MAX_PHOTO_BYTES = 6 * 1024 * 1024   # лимит на вложение, чтобы письмо не отклонили

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}

def _image_subtype(filename: str) -> str:
    """Определяем подтип по расширению (нужно для MIMEImage)."""
    ext = os.path.splitext(filename)[1].lower()
    return {
        ".jpg": "jpeg",
        ".jpeg": "jpeg",
        ".png": "png",
        ".webp": "webp",
        ".gif": "gif",
        ".heic": "heic",
        ".heif": "heif",
    }.get(ext, "jpeg")

def _build_message(name, phone, product_type, photos):
    """Собирает письмо. photos — список кортежей (filename, bytes)."""
    subject = f"Новая заявка на перила: {name}"

    body = (
        "Поступила новая заявка с сайта Вектор-Пролет\n\n"
        f"Имя клиента: {name}\n"
        f"Телефон: {phone}\n"
        f"Что необходимо сделать: {product_type}\n"
    )
    if photos:
        body += f"\nПриложено фото: {len(photos)} шт.\n"
    body += "\nПожалуйста, свяжитесь с клиентом в течение 15 минут."

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = TARGET_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    for filename, data in photos:
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext in ALLOWED_EXT:
                part = MIMEImage(data, _subtype=_image_subtype(filename))
            else:
                part = MIMEApplication(data, _subtype="octet-stream")
            part.add_header(
                'Content-Disposition', 'attachment',
                filename=('utf-8', '', filename),   # корректные русские имена
            )
            msg.attach(part)
        except Exception as e:
            app.logger.warning("Не удалось прикрепить %s: %s", filename, e)

    return msg

def send_to_email(name, phone, product_type, photos=None):
    """Отправка заявки. Возвращает (успех: bool, текст_ошибки: str|None)."""
    if not SMTP_PASSWORD:
        app.logger.error("SMTP_PASSWORD не задан в переменных окружения!")
        return False, "SMTP_PASSWORD не задан"

    photos = photos or []
    msg = _build_message(name, phone, product_type, photos)

    try:
        # Таймаут обязателен: без него запрос висит и Render отдаёт 504
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, [TARGET_EMAIL], msg.as_string())
        app.logger.info("Заявка отправлена на %s", TARGET_EMAIL)
        return True, None
    except smtplib.SMTPAuthenticationError as e:
        app.logger.error("Ошибка авторизации SMTP: %s", e)
        return False, "auth"
    except smtplib.SMTPException as e:
        app.logger.error("SMTP-ошибка: %s", e)
        return False, "smtp"
    except (OSError, TimeoutError) as e:
        app.logger.error("Сетевая ошибка SMTP: %s", e)
        return False, "network"
    except Exception as e:
        app.logger.exception("Неизвестная ошибка отправки: %s", e)
        return False, "unknown"

def _background_send(name, phone, product_type, photos):
    """Отправка в фоне, чтобы клиент не ждал SMTP."""
    try:
        send_to_email(name, phone, product_type, photos)
    except Exception as e:
        app.logger.exception("Ошибка в фоновой отправке: %s", e)

THANK_YOU_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Заявка принята — Вектор-Пролет</title>
</head>
<body style="margin:0;background:#f8fafc;font-family:system-ui,-apple-system,sans-serif;">
  <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;">
    <div style="background:#fff;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(15,23,42,.08);max-width:480px;text-align:center;">
      <h1 style="color:#0f172a;font-size:22px;margin:0 0 12px;">Заявка успешно принята</h1>
      <p style="color:#64748b;margin:0 0 24px;line-height:1.5;">
        Мы получили вашу заявку и свяжемся с вами в течение 15 минут.
      </p>
      <a href="/" style="display:inline-block;padding:14px 28px;background:#f59e0b;color:#0f172a;text-decoration:none;border-radius:8px;font-weight:700;">Вернуться на сайт</a>
    </div>
  </div>
</body>
</html>
"""

ERROR_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ошибка — Вектор-Пролет</title>
</head>
<body style="margin:0;background:#f8fafc;font-family:system-ui,-apple-system,sans-serif;">
  <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;">
    <div style="background:#fff;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(15,23,42,.08);max-width:480px;text-align:center;">
      <h1 style="color:#ef4444;font-size:22px;margin:0 0 12px;">Не удалось отправить заявку</h1>
      <p style="color:#64748b;margin:0 0 24px;line-height:1.5;">
        Пожалуйста, позвоните нам напрямую или попробуйте отправить форму ещё раз через минуту.
      </p>
      <a href="/" style="display:inline-block;padding:14px 28px;background:#f59e0b;color:#0f172a;text-decoration:none;border-radius:8px;font-weight:700;">Назад на сайт</a>
    </div>
  </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-request', methods=['POST'])
def submit_request():
    name = (request.form.get('name') or '').strip()
    phone = (request.form.get('phone') or '').strip()
    product_type = (request.form.get('product_type') or '').strip()

    # Валидация: не отправляем письмо с пустыми полями
    if not name or not phone:
        return ERROR_PAGE, 400

    # Собираем фотографии (поддерживаем и одно поле, и multiple)
    photos = []
    total_size = 0
    for f in request.files.getlist('photo'):
        if not f or not f.filename:
            continue
        data = f.read()
        total_size += len(data)
        if total_size > MAX_PHOTO_BYTES:
            app.logger.warning("Превышен лимит вложений, часть фото отброшена")
            break
        photos.append((f.filename, data))

    # Синхронно, но с таймаутом 10 с. Если хотите мгновенный ответ —
    # раскомментируйте фоновый вариант ниже.
    ok, reason = send_to_email(name, phone, product_type, photos)

    # ---- Фоновый вариант (ответ клиенту мгновенно) ----
    # threading.Thread(
    #     target=_background_send,
    #     args=(name, phone, product_type, photos),
    #     daemon=True,
    # ).start()
    # ok, reason = True, None

    if not ok:
        app.logger.error("Отправка не удалась, причина: %s", reason)
        return ERROR_PAGE, 500

    return THANK_YOU_PAGE

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.errorhandler(413)
def too_large(e):
    return ERROR_PAGE, 413

@app.errorhandler(500)
def server_error(e):
    return ERROR_PAGE, 500

if __name__ == '__main__':
    # Локальный запуск. На Render используется gunicorn (см. ниже).
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
