import asyncio
import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.enabled = settings.EMAIL_ENABLED
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM

    def _validate_configuration(self) -> None:
        if not self.smtp_username:
            raise ValueError(
                "SMTP_USERNAME is not configured."
            )

        if not self.smtp_password:
            raise ValueError(
                "SMTP_PASSWORD is not configured."
            )

        if not self.email_from:
            raise ValueError(
                "EMAIL_FROM is not configured."
            )

    def _send_smtp_message(
        self,
        message: EmailMessage,
    ) -> None:
        with smtplib.SMTP(
            self.smtp_host,
            self.smtp_port,
            timeout=20,
        ) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            smtp.login(
                self.smtp_username,
                self.smtp_password,
            )

            smtp.send_message(message)

    async def send_email(
        self,
        *,
        recipient: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> dict:
        if not recipient or "@" not in recipient:
            raise ValueError(
                "A valid recipient email is required."
            )

        if not subject.strip():
            raise ValueError(
                "Email subject cannot be empty."
            )

        if not html_content.strip():
            raise ValueError(
                "Email content cannot be empty."
            )

        if not self.enabled:
            logger.info(
                "Mock email generated for %s",
                recipient,
            )

            return {
                "success": True,
                "status": "mock",
                "recipient": recipient,
                "subject": subject,
                "message": (
                    "Email generated successfully "
                    "in development mode."
                ),
            }

        self._validate_configuration()

        message = EmailMessage()

        message["From"] = formataddr(
            (
                "RRVDXB Store",
                self.email_from,
            )
        )
        message["To"] = recipient
        message["Subject"] = subject

        message.set_content(
            text_content
            or "Please view this email in HTML format."
        )

        message.add_alternative(
            html_content,
            subtype="html",
        )

        try:
            await asyncio.to_thread(
                self._send_smtp_message,
                message,
            )

            return {
                "success": True,
                "status": "sent",
                "recipient": recipient,
                "subject": subject,
                "message": (
                    "Email sent successfully."
                ),
            }

        except (
            smtplib.SMTPException,
            OSError,
        ) as exception:
            logger.exception(
                "Email sending failed"
            )

            return {
                "success": False,
                "status": "failed",
                "recipient": recipient,
                "subject": subject,
                "message": str(exception),
            }

    async def send_order_confirmation(
        self,
        *,
        recipient: str,
        customer_name: str,
        order_number: str,
        total_amount: float,
    ) -> dict:
        subject = (
            f"RRVDXB Order Confirmation "
            f"- {order_number}"
        )

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #1A1A1A;">
                Order Confirmed
            </h2>

            <p>Hello {customer_name},</p>

            <p>
                Thank you for shopping with RRVDXB.
                Your order has been received successfully.
            </p>

            <p>
                <strong>Order Number:</strong>
                {order_number}
            </p>

            <p>
                <strong>Total Amount:</strong>
                AED {total_amount:.2f}
            </p>

            <p>
                We will notify you when your order
                has been shipped.
            </p>

            <p>RRVDXB Premium Online Store</p>
        </body>
        </html>
        """

        text_content = (
            f"Hello {customer_name}, "
            f"your RRVDXB order {order_number} "
            f"has been confirmed. "
            f"Total: AED {total_amount:.2f}."
        )

        return await self.send_email(
            recipient=recipient,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )


email_service = EmailService()