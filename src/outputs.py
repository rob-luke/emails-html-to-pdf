

from abc import abstractmethod
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path
import smtplib
import logging


class AbstractOutput:

    @abstractmethod
    def process(self, originalMessage, generatedPdfs):
        """Process the output of the email conversion

        Args:
            originalMessage (???): The original message which was converted
            generatedPdfs (list[str]): A list of file paths to the PDFs generated from the email
        """
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

class SendOutputByEmail:
    """Sends output to an email address

    Args:
        mail_from (str): from name
        mail_to (str): to name(s)
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        encryption (str): Type of encryption to use (if any)
    """
    SMTP_ENCRYPTION_STARTTLS="STARTTLS"
    SMTP_ENCRYPTION_SSL="SSL"

    __logger = logging.getLogger(__name__)

    def __init__(self, mail_from, mail_to, server, port, username, password, encryption):
        self.__mail_from = mail_from
        self.__mail_to = mail_to
        self.__server = server
        self.__port = port
        self.__username = username
        self.__password = password
        self.__encryption = encryption

    def __enter__(self):
        self.__logger.info(f"Connecting to SMTP server {self.__server}:{self.__port}...")
        if self.__encryption == self.SMTP_ENCRYPTION_SSL:
            self.__logger.debug(f"Using SSL encryption for SMTP")
            self.__smtp = smtplib.SMTP_SSL(self.__server, self.__port)
        else:
            self.__smtp = smtplib.SMTP(self.__server, self.__port)

        if self.__encryption == self.SMTP_ENCRYPTION_STARTTLS:
            self.__logger.debug(f"Using STARTTLS encryption for SMTP")
            self.__smtp.starttls()

        self.__logger.debug(f"Logging in to SMTP server as {self.__username}...")
        self.__smtp.login(self.__username, self.__password)

        self.__logger.info("SMTP setup successful")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__logger.debug("Closing SMTP server connection...")
        self.__smtp.quit()
        self.__logger.info("SMTP server closed gracefully")

    def process(self, originalMessage, generatedPdfs):
        logging.debug(f"Building output email for '{originalMessage.subject}'...")
        msg = MIMEMultipart()
        msg["From"] = self.__mail_from
        msg["To"] = self.__mail_to
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = originalMessage.subject

        message = f"Converted PDF of email from {originalMessage.from_} on {originalMessage.date_str} wih topic {originalMessage.subject}. Content below.\n\n\n\n{originalMessage.text}"
        msg.attach(MIMEText(message))

        for path in generatedPdfs:
            part = MIMEBase("application", "octet-stream")
            with open(path, "rb") as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=format(Path(path).name),
            )
            msg.attach(part)

        logging.info(f"Sending PDF output for '{originalMessage.subject}' to '{self.__mail_to}...")
        self.__smtp.sendmail(self.__mail_from, self.__mail_to, msg.as_string())
        logging.info(f"Sent PDF output for '{originalMessage.subject}' to '{self.__mail_to}...")
