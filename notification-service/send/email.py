import smtplib
import os
import json
import logging
from email.message import EmailMessage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def notification(message):
    try:
        # Проверка входных данных
        message = json.loads(message)
        if not message or "mp3_fid" not in message or "username" not in message:
            logger.error("Invalid message format")
            return "Invalid message format"

        mp3_fid = message["mp3_fid"]
        sender_address = os.getenv("GMAIL_ADDRESS")
        sender_password = os.getenv("GMAIL_PASSWORD")
        receiver_address = message["username"]

        # Создание письма
        msg = EmailMessage()
        msg.set_content(f"mp3 file_id: {mp3_fid} is now ready!")  # Plain text
        msg.add_alternative(f"""
        <html>
            <body>
                <p>Your MP3 file is now ready!</p>
                <p>File ID: <strong>{mp3_fid}</strong></p>
            </body>
        </html>
        """, subtype="html")  # HTML content
        msg["Subject"] = "MP3 Download"
        msg["From"] = sender_address
        msg["To"] = receiver_address

        # Отправка письма
        with smtplib.SMTP("smtp.gmail.com", 587) as session:
            session.starttls()
            session.login(sender_address, sender_password)
            session.send_message(msg)
            logger.info("Mail sent successfully")

    except smtplib.SMTPAuthenticationError:
        logger.error("Failed to authenticate with Gmail. Check your credentials.")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")