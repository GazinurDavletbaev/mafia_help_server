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

    # ✅ ИСПРАВЛЕНО — ссылка на приложение
    link = f"mafiahelp://verify-email?token={token}"
    print(f"🔗 Ссылка: {link}")

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = email
    msg['Subject'] = "Подтверждение email — Mafia Help"

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 500px;">
        <h2 style="color: #f58b20;">Подтверждение email</h2>
        <p>Чтобы подтвердить свой email, нажмите на кнопку ниже:</p>
        <a href="{link}" style="display: inline-block; background: #f58b20; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">Подтвердить email</a>
        <p style="color: #666; font-size: 12px; margin-top: 20px;">Ссылка действует 24 часа.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        print("📧 Подключаюсь к SMTP серверу...")
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        print("✅ Подключено")
        
        print("📧 Логинюсь...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("✅ Логин успешен")
        
        print("📧 Отправляю письмо...")
        server.send_message(msg)
        print("✅ Письмо отправлено")
        
        server.quit()
        print("📧 Соединение закрыто")
        print("=" * 60)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ ОШИБКА АВТОРИЗАЦИИ: {e}")
        print("   Проверь SMTP_USER и SMTP_PASSWORD")
        print("=" * 60)
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ ОШИБКА SMTP: {e}")
        print("=" * 60)
        return False
        
    except Exception as e:
        print(f"❌ НЕИЗВЕСТНАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False


def send_reset_password_email(email: str, token: str):
    """Отправка письма для сброса пароля"""
    print("=" * 60)
    print("📧 ОТПРАВКА ПИСЬМА ДЛЯ СБРОСА ПАРОЛЯ")
    print("=" * 60)
    print(f"📧 Кому: {email}")
    print(f"📧 Токен: {token}")

    # ✅ ИСПРАВЛЕНО — ссылка на приложение
    link = f"mafiahelp://reset-password?token={token}"
    print(f"🔗 Ссылка: {link}")

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = email
    msg['Subject'] = "Восстановление пароля — Mafia Help"

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 500px;">
        <h2 style="color: #f58b20;">Восстановление пароля</h2>
        <p>Вы запросили сброс пароля. Нажмите на кнопку ниже, чтобы установить новый пароль:</p>
        <a href="{link}" style="display: inline-block; background: #f58b20; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">Сбросить пароль</a>
        <p style="color: #666; font-size: 12px; margin-top: 20px;">Ссылка действует 24 часа.</p>
        <p style="color: #999; font-size: 12px;">Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        print("📧 Подключаюсь к SMTP...")
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        print("✅ Подключено")
        
        print("📧 Логинюсь...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("✅ Логин успешен")
        
        print("📧 Отправляю письмо...")
        server.send_message(msg)
        print("✅ Письмо отправлено")
        
        server.quit()
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        print("=" * 60)
        return False