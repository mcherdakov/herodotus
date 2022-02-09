from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr

from app.senders.models import Message
from app.settings import settings

email_sender_conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=EmailStr(settings.mail_username),
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_TLS=settings.mail_tls,
    MAIL_SSL=settings.mail_ssl,
    USE_CREDENTIALS=settings.mail_use_credentials,
    VALIDATE_CERTS=settings.mail_validatae_certs,
)


async def send_emails(emails: list[EmailStr], message: Message):
    schema = MessageSchema(subject=message.title, recipients=emails, body=message.text)
    fm = FastMail(email_sender_conf)
    await fm.send_message(schema)
