import io
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

# Загружаем скрытые переменные из файла .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-for-flash")

# НАСТРОЙКА ПОЧТЫ MAIL.RU
SMTP_SERVER = "smtp.mail.ru"
SMTP_PORT = 465

SENDER_EMAIL = "o.p.f.1994@mail.ru"
TARGET_EMAIL = "o.p.f.1994@mail.ru"

# ВАЖНО: Здесь должен быть "Пароль для внешних приложений", а не обычный пароль от почты!
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_to_email(name, phone, product_type, file_data=None, file_name=None):
    """Функция автоматической отправки заявки и вложенного фото на ваш Email"""
    subject = f"🚨 Новая заявка на перила: {name}"
    body = (
        f"Поступила новая заявка с сайта Вектор-Пролет тк!\n\n"
        f"👤 Имя клиента: {name}\n"
        f"📞 Номер телефона: {phone}\n"
        f"📐 Что необходимо сделать: {product_type}\n\n"
        f"⚡ Пожалуйста, свяжитесь с клиентом в течение 15 минут."
    )

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = TARGET_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # 📷 НАДЕЖНОЕ ДОБАВЛЕНИЕ ЛЮБЫХ ИЗОБРАЖЕНИЙ (БЕЗ ОШИБОК 500)
    if file_data and file_name:
        try:
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(file_data)
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition", f'attachment; filename="{file_name}"'
            )
            msg.attach(attachment)
            print(
                f"Файл {file_name} успешно зашифрован и прикреплен к письму."
            )
        except Exception as e:
            print(f"Не удалось прикрепить файл к письму: {e}")

    # Завершение оборванного участка кода
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, TARGET_EMAIL, msg.as_string())
        print("Письмо успешно отправлено!")
        return True
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")
        return False


# ПРИМЕР МАРШРУТА ДЛЯ ПРИЕМА ФОРМЫ С САЙТА
@app.route("/submit-form", methods=["POST"])
def handle_form():
    """Принимает данные формы и передает файл из памяти (без сохранения на диск)"""
    name = request.form.get("name")
    phone = request.form.get("phone")
    product_type = request.form.get("product_type")

    # Получаем файл из инпута (например, <input type="file" name="photo">)
    file = request.files.get("photo")

    file_data = None
    file_name = None

    if file and file.filename != "":
        # Читаем файл в бинарный поток в памяти сервера
        file_data = file.read()
        file_name = file.filename

    # Вызываем функцию отправки
    success = send_to_email(
        name, phone, product_type, file_data=file_data, file_name=file_name
    )

    if success:
        return "Заявка успешно отправлена! Свяжемся с вами в течение 15 минут."
    else:
        return (
            "Произошла ошибка при отправке заявки. Пожалуйста, попробуйте позже.",
            500,
        )


if __name__ == "__main__":
    app.run(debug=True)
