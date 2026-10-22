import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request

app = Flask(__name__)

# ⚠️ НАСТРОЙКА ПОЧТЫ MAIL.RU
SMTP_SERVER = "smtp.mail.ru"
SMTP_PORT = 465

# Отправляем письмо с вашей почты самому себе
SENDER_EMAIL = "o.p.f.1994@mail.ru"
TARGET_EMAIL = "o.p.f.1994@mail.ru"

# 🔑 Сюда вставьте ваш 16-значный пароль приложения из настроек Mail.ru
SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"


def send_to_email(name, phone, product_type):
    """Функция автоматической отправки заявки на ваш Email"""
    subject = f"🚨 Новая заявка на перила: {name}"
    body = (
        f"Поступила новая заявка с сайта Вектор-Пролет!\n\n"
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

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, TARGET_EMAIL, msg.as_string())
        print("Заявка успешно отправлена на o.p.f.1994@mail.ru")
    except Exception as e:
        print(f"Ошибка при отправке почты: {e}")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit-request', methods=['POST'])
def submit_request():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        product_type = request.form.get('product_type')

        # Запуск отправки письма
        send_to_email(name, phone, product_type)

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


if __name__ == '__main__':
    app.run(debug=True)
