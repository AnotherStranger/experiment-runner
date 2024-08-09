"""
This module provides mailing related functionalities.
"""

# pylint: disable=too-few-public-methods
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

from experiment_runner.processing.configurator import Configurator


class Mailer:
    """
    Mailer class for sending emails.
    """

    def send(self, subject: str, body: str, attachment_path: Optional[Path] = None):
        """
        Sends an email to the recipients in MailerConfig

        Args:
            subject: The subject of the email
            body: The body of the email
            attachment_path: The path to the attachment which will be attached to the email
        """
        subject_encoded = subject.encode("utf-8", "ignore").decode("utf-8")
        body_encoded = body.encode("utf-8", "ignore").decode("utf-8")
        config = Configurator().config

        with smtplib.SMTP(config.host, config.port) as smtp:
            smtp.starttls()
            smtp.login(config.username, config.password)

            message = MIMEMultipart("alternative")
            message["Subject"] = subject_encoded
            message["From"] = config.from_email
            message["To"] = config.to_email

            message.add_header("Content-Type", "text/html")
            part1 = MIMEText(body_encoded, "html", "utf-8")

            message.attach(part1)

            if attachment_path:
                self.add_attachment(attachment_path, message, trim=True)

            smtp.send_message(message)

    def add_attachment(self, attachment_path: Path, message: MIMEMultipart, trim: bool = False):
        """
        Adds a file attachment to the message as base64 mime part
        """
        if trim:
            attachment_path = self.trim_file_to_size(attachment_path, 20)
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={attachment_path.name}")
            message.attach(part)

    def trim_file_to_size(self, file_path: Path, max_size_mb: int) -> Path:
        """
        20MB is allowed for mails. Trim the logfile.
        """
        max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        total_size = 0

        if file_path.stat().st_size <= max_size_bytes:
            return file_path

        lines: List[str] = []
        with open(file_path, "r", encoding="utf-8") as file:
            lines.extend(file.readlines())

        truncated_lines = []

        # Add lines from the end until the size exceeds the limit
        for line in reversed(lines):
            line_size = len(line.encode("utf-8"))
            if total_size + line_size <= max_size_bytes:
                truncated_lines.append(line)
                total_size += line_size
            else:
                break

        # Reverse the lines back to original order
        truncated_lines.reverse()

        trimmed_file_path = file_path.with_name(file_path.stem + "_trimmed" + file_path.suffix)
        with open(trimmed_file_path, "w", encoding="utf-8") as f:
            f.writelines(truncated_lines)

        return trimmed_file_path
