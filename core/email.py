import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========== НАСТРОЙКИ SMTP ==========
SMTP_HOST = "smtp.mail.ru"
SMTP_PORT = 465
SMTP_USER = "gyxtochka@mail.ru"
SMTP_PASSWORD = "Qxrmo8di1f6SEJ08CMnA"

def send_verification_email(email: str, token: str):
    print("=" * 60)
    print("📧 НАЧАЛО ОТПРАВКИ ПИСЬМА")
    print("=" * 60)
    print(f"📧 Кому: {email}")
    print(f"📧 Токен: {token}")

    # 🔥 ДВЕ ССЫЛКИ
    deep_link = f"mafiahelp://verify-email?token={token}"
    web_link = f"http://161.104.46.234/verify-email?token={token}"

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = email
    msg['Subject'] = "Подтверждение email — Mafia Help"

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 500px;">
        <h2 style="color: #f58b20;">Подтверждение email</h2>
        <p>Чтобы подтвердить свой email, выберите удобный способ:</p>

        <!-- 🔥 ВАРИАНТ 1: КНОПКА (для телефона с приложением) -->
        <a href="{deep_link}" 
           style="display: inline-block; background: #f58b20; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-bottom: 12px;">
           📱 Подтвердить в приложении
        </a>

        <p style="color: #999; font-size: 13px; margin: 8px 0;">
           <em>или</em>
        </p>

        <!-- 🔥 ВАРИАНТ 2: ССЫЛКА (для компьютера / браузера) -->
        <p style="font-size: 14px;">
           <a href="{web_link}" style="color: #f58b20; word-break: break-all;">
              {web_link}
           </a>
        </p>

        <p style="color: #666; font-size: 12px; margin-top: 20px;">
           Ссылка действительна 24 часа.
        </p>
        <p style="color: #999; font-size: 11px;">
           Если вы не регистрировались в Mafia Help, просто проигнорируйте это письмо.
        </p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ Письмо отправлено")
        return True
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

def send_reset_code_email(email: str, code: str):
    print("=" * 60)
    print("📧 ОТПРАВКА КОДА ДЛЯ СБРОСА ПАРЛЯ")
    print("=" * 60)
    print(f"📧 Кому: {email}")
    print(f"📧 Код: {code}")

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = email
    msg['Subject'] = "Код для сброса пароля — Mafia Help"

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 500px;">
        <h2 style="color: #f58b20;">Код для сброса пароля</h2>
        <p>Ваш код для сброса пароля:</p>
        <h1 style="font-size: 36px; letter-spacing: 4px; color: #f58b20;">{code}</h1>
        <p style="color: #666; font-size: 12px; margin-top: 20px;">Код действует 15 минут.</p>
        <p style="color: #999; font-size: 12px;">Введите код в приложении, чтобы сбросить пароль.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ Письмо с кодом отправлено")
        return True
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False
