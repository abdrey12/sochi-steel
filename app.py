import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase  # Изменено на универсальный тип вложений
from email import encoders  # Библиотека шифрования файлов для интернета
import io  # Библиотека для чтения файлов в памяти сервера
import os
from flask import Flask, render_template, request
from dotenv import load_dotenv

# Загружаем скрытые переменные из файла .env
load_dotenv()

app = Flask(__name__)

# НАСТРОЙКА ПОЧТЫ MAIL.RU
SMTP_SERVER = "smtp.mail.ru"
SMTP_PORT = 465

SENDER_EMAIL = "o.p.f.1994@mail.ru"
TARGET_EMAIL = "o.p.f.1994@mail.ru"

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
    msg['From'] = SENDER_EMAIL
    msg['To'] = TARGET_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # 📷 НАДЕЖНОЕ ДОБАВЛЕНИЕ ЛЮБЫХ ИЗОБРАЖЕНИЙ (БЕЗ ОШИБОК 500)
    if file_data and file_name:
        try:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(file_data)
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', f'attachment; filename="{file_name}"')
            msg.attach(attachment)
            print(f"Файл {file_name} успешно зашифрован и прикреплен к письму.")
        except Exception as e:
            print(f"Не удалось прикрепить файл к письму: {e}")

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, TARGET_EMAIL, msg.as_string())
        print(f"Заявка успешно отправлена на {TARGET_EMAIL}")
        return True
    except Exception as e:
        print(f"Ошибка при отправке почты: {e}")
        return False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit-request', methods=['POST'])
def submit_request():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        product_type = request.form.get('product_type')

        # 📥 Получаем файл фотографии из формы сайта безопасным методом
        uploaded_file = request.files.get('photo')
        file_data = None
        file_name = None

        if uploaded_file and uploaded_file.filename != '':
            file_data = uploaded_file.read()
            # Переводим имя файла в безопасный формат для почтовых серверов
            file_name = uploaded_file.filename.encode('utf-8').decode('latin-1', 'ignore')

        # Запуск отправки письма (передаем тексты и файл)
        mail_success = send_to_email(name, phone, product_type, file_data, file_name)

        if not mail_success:
            return """
            <div style="text-align: center; font-family: sans-serif; padding-top: 100px;">
                <h2 style="color: #ef4444;">❌ Ошибка отправки</h2>
                <p>Что-то пошло не так при отправке уведомления. Мы разберемся с этим. Пожалуйста, попробуйте позже.</p>
                <a href="/">Назад</a>
            </div>
            """

        # Страница благодарности для клиента
        return """
        <div style="text-align: center; font-family: sans-serif; padding-top: 100px; background-color: #f8fafc; height: 100vh; margin: 0;">
            <div style="background: white; display: inline-block; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
                <h2 style="color: #0f172a; margin-bottom: 10px;">🔥 Заявка успешно принята!</h2>
                <p style="color: #64748b; margin-bottom: 25px;">Мы уже получили уведомление и свяжемся с вами в течение 15 минут.</p>
                <a href="/" style="display: inline-block; padding: 12px 24px; background: #f59e0b; color: #0f172a; text-decoration: none; border-radius: 6px; font-weight: bold;">Вернуться на сайт</a>
            </div>
        </div>
        """


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


if __name__ == '__main__':
    app.run(debug=True)
