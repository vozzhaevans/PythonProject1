import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailNotifier:

    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_notification(self, to_email: str, subject: str, body: str,
                          from_email: str = None, password: str = None):

        if not from_email or not password:
            print(" Не указаны данные для SMTP")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
            server.quit()

            print(f" Уведомление отправлено на {to_email}")
            return True
        except Exception as e:
            print(f" Ошибка отправки email: {e}")
            return False


def send_change_notification(to_email, from_email, password, new_count, changes):
    notifier = EmailNotifier()
    subject = f"ЦИАН: Изменения в объявлениях ({new_count} шт.)"

    body = f"""Обнаружены изменения на ЦИАН!

Дата/время: {datetime.now().strftime('%d.%m.%Y %H:%M')}

Найдено объявлений сейчас: {new_count}

Изменения:
{changes}

Ссылка для просмотра: https://ekb.cian.ru/snyat-kvartiru/
"""

    return notifier.send_notification(to_email, subject, body, from_email, password)