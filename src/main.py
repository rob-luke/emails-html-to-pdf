#!/usr/bin/env python

import pdfkit
from imap_tools import MailBox, AND, MailMessageFlags
import os
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders


def send_mail(send_from, send_to, subject, message, files=[],
              server=None, port=587,
              username=None,
              password=None,
              use_tls=True):
    """Compose and send email with provided info and attachments.

    Args:
        send_from (str): from name
        send_to (str): to name(s)
        subject (str): message title
        message (str): message body
        files (list[str]): list of file paths to be attached to email
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        use_tls (bool): use TLS mode
    """
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message))

    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename={}'.format(Path(path).name))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


def process_mail(mark_read=True, num_emails_limit=50, imap_url=None, imap_username=None, imap_password=None, imap_folder=None, mail_sender=None, server_smtp=None, mail_destination=None):
    print("Starting mail processing run", flush=True)

    with MailBox(imap_url).login(imap_username, imap_password, imap_folder) as mailbox:
        for i, msg in enumerate(mailbox.fetch(criteria=AND(seen=False), limit=num_emails_limit, mark_seen=False)):
            if len(msg.attachments) == 0:
                print(f"\nNo attachments in: {msg.subject}")
                html = '<meta http-equiv="Content-type" content="text/html; charset=utf-8"/>' + msg.html
                filename = f'{msg.subject}.pdf'
                for bad_char in ["/", "*", ":", "<", ">", "|", '"', '.', '_']:
                    filename = filename.replace(bad_char, "_")
                pdfkit.from_string(html, filename)
                send_mail(mail_sender,
                          mail_destination,
                          f"{msg.subject}",
                          f"Converted PDF of email from {msg.from_} on {msg.date_str} wih topic {msg.subject}. Content below.\n\n\n\n{msg.text}",
                          files=[filename], server=server_smtp, username=imap_username, password=imap_password)
                if mark_read:
                    mailbox.flag(msg.uid, MailMessageFlags.SEEN, True)
                os.remove(filename)
    print("Completed mail processing run\n\n", flush=True)


if __name__ == '__main__':

    server_imap = os.environ.get("IMAP_URL")
    username = os.environ.get("IMAP_USERNAME")
    password = os.environ.get("IMAP_PASSWORD")
    folder = os.environ.get("IMAP_FOLDER")

    server_smtp = os.environ.get("SMTP_URL")

    sender = os.environ.get("MAIL_SENDER")
    destination = os.environ.get("MAIL_DESTINATION")

    print("Running emails-html-to-pdf")

    process_mail(imap_url=server_imap,
                 imap_username=username,
                 imap_password=password,
                 imap_folder=folder,
                 mail_sender=sender,
                 mail_destination=destination,
                 server_smtp=server_smtp)
