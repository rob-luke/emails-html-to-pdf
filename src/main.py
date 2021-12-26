#!/usr/bin/env python

import pdfkit
import json
from imap_tools import MailBox, AND, MailMessageFlags
import os
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders


def send_mail(
    send_from,
    send_to,
    subject,
    message,
    files=[],
    server=None,
    port=None,
    username=None,
    password=None,
    use_tls=None,
):
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
    msg["From"] = send_from
    msg["To"] = send_to
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    msg.attach(MIMEText(message))

    for path in files:
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

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


def process_mail(
    mark_msg=True,
    num_emails_limit=50,
    imap_url=None,
    imap_username=None,
    imap_password=None,
    imap_folder=None,
    mail_sender=None,
    server_smtp=None,
    smtp_tls=None,
    smtp_port=None,
    mail_destination=None,
    printfailedmessage=None,
    pdfkit_options=None,
    mail_msg_flag=None,
    filter_criteria=AND(seen=False),
):
    print("Starting mail processing run", flush=True)
    if printfailedmessage:
        print("*On failure, the Body of the email will be printed*")

    PDF_CONTENT_ERRORS = [
        "ContentNotFoundError",
        "ContentOperationNotPermittedError",
        "UnknownContentError",
        "RemoteHostClosedError",
        "ConnectionRefusedError",
        "Server refused a stream",
    ]

    with MailBox(imap_url).login(imap_username, imap_password, imap_folder) as mailbox:
        for i, msg in enumerate(
            mailbox.fetch(
                criteria=filter_criteria,
                limit=num_emails_limit,
                mark_seen=False,
            )
        ):
            if len(msg.attachments) == 0:
                print(f"\nNo attachments in: {msg.subject}")
                if not msg.html.strip() == "":  # handle text only emails
                    pdftext = (
                        '<meta http-equiv="Content-type" content="text/html; charset=utf-8"/>'
                        + msg.html
                    )
                else:
                    pdftext = msg.text
                filename = f'{msg.subject.replace(".", "_").replace(" ", "-")[:50]}.pdf'
                print(f"\nPDF: {filename}")
                for bad_char in ["/", "*", ":", "<", ">", "|", '"', "’", "–"]:
                    filename = filename.replace(bad_char, "_")
                print(f"\nPDF: {filename}")
                options = {}
                if pdfkit_options is not None:
                    # parse WKHTMLTOPDF Options to dict
                    options = json.loads(pdfkit_options)
                try:
                    pdfkit.from_string(pdftext, filename, options=options)
                except OSError as e:
                    if any([error in str(e) for error in PDF_CONTENT_ERRORS]):
                        # allow pdfs with missing images if file got created
                        if os.path.exists(filename):
                            if printfailedmessage:
                                print(f"\n{pdftext}\n")
                            print(f"\n **** HANDLED EXCEPTION ****")
                            print(f"\n\n{str(e)}\n")
                            print(
                                f"\nError with images in file, continuing without them.  Email Body/HTML Above"
                            )

                        else:
                            if printfailedmessage:
                                print(f"\n{pdftext}\n")
                            print(
                                f"\n !!!! UNHANDLED EXCEPTION with PDF Content Errors: {PDF_CONTENT_ERRORS} !!!!"
                            )
                            print(f"\n{str(e)}")
                            print(f"\nBody/HTML Above")
                            raise e
                    else:
                        if printfailedmessage:
                            print(f"\n{pdftext}\n")
                        print(f"\n !!!! UNHANDLED EXCEPTION !!!!")
                        print(f"\n{str(e)}")
                        print(f"\nBody/HTML Above")
                        raise e

                send_mail(
                    mail_sender,
                    mail_destination,
                    f"{msg.subject}",
                    f"Converted PDF of email from {msg.from_} on {msg.date_str} wih topic {msg.subject}. Content below.\n\n\n\n{msg.text}",
                    files=[filename],
                    server=server_smtp,
                    username=imap_username,
                    password=imap_password,
                    port=smtp_port,
                    use_tls=smtp_tls,
                )

                if mark_msg and mail_msg_flag and mail_msg_flag[0] in MailMessageFlags.all:
                    mailbox.flag(msg.uid, mail_msg_flag[0], mail_msg_flag[1])
                os.remove(filename)
    print("Completed mail processing run\n\n", flush=True)


def _get_mail_message_flag():
    """Determine mail message flag to set on processed emails from environment variable.
    
    Only valid options are "ANSWERED", "FLAGGED", "UNFLAGGED", "DELETED" and "SEEN". Any other values will default to "SEEN".

    DRAFT flag is excluded as it can cause strange behaviour with inbound mail becoming outbound.
    RECENT flag is excluded as it is read-only

    Returns a tuple. The first part is the flag and the second is if it should be added (True) or removed (False).
    """
    mail_message_flag = os.environ.get("MAIL_MESSAGE_FLAG", 'SEEN').upper()
    if mail_message_flag == "ANSWERED":
        return (MailMessageFlags.ANSWERED, True)
    elif mail_message_flag == "FLAGGED":
        return (MailMessageFlags.FLAGGED, True)
    elif mail_message_flag == "UNFLAGGED":
        return (MailMessageFlags.FLAGGED, False)
    elif mail_message_flag == "DELETED":
        return (MailMessageFlags.DELETED, True)
    else:
        return (MailMessageFlags.SEEN, True)


def _get_imap_filter(mail_message_flag):
    """Determine mail message filter to apply when searching for mail from environment variable.

    If no environment variable is provided, a suitable value is determined from the mail message flag.
    If no suitable value can be determined, an error is raised.
    """
    raw_filter_criteria = os.environ.get("IMAP_FILTER")
    if raw_filter_criteria:
        return raw_filter_criteria

    # No value specified so generate a default from the message flag
    if mail_message_flag[0] == MailMessageFlags.SEEN:
        return AND(seen=(not mail_message_flag[1]))
    elif mail_message_flag[0] == MailMessageFlags.ANSWERED:
        return AND(answered=(not mail_message_flag[1]))
    elif mail_message_flag[0] == MailMessageFlags.FLAGGED:
        return AND(flagged=(not mail_message_flag[1]))
    elif mail_message_flag[0] == MailMessageFlags.DELETED and mail_message_flag[1]:
        # Search for undeleted while possible doesn't make sense
        # so just search for all
        return AND(all=True)
    else:
        # Can't determine an appropriate value so make the user supply one
        raise ValueError("Could not determine IMAP filter from mail message flag. You must specify the filter manually.")


if __name__ == "__main__":

    server_imap = os.environ.get("IMAP_URL")
    username = os.environ.get("IMAP_USERNAME")
    password = os.environ.get("IMAP_PASSWORD")
    folder = os.environ.get("IMAP_FOLDER")

    server_smtp = os.environ.get("SMTP_URL")
    sender = os.environ.get("MAIL_SENDER")
    destination = os.environ.get("MAIL_DESTINATION")
    smtp_port = os.getenv("SMTP_PORT", 587)
    smtp_tls = os.getenv("SMTP_TLS", True)

    printfailedmessage = os.getenv("PRINT_FAILED_MSG", "False") == "True"
    pdfkit_options = os.environ.get("WKHTMLTOPDF_OPTIONS")
    mail_msg_flag = _get_mail_message_flag()

    filter_criteria = _get_imap_filter(mail_msg_flag)

    print("Running emails-html-to-pdf")

    process_mail(
        imap_url=server_imap,
        imap_username=username,
        imap_password=password,
        imap_folder=folder,
        mail_sender=sender,
        mail_destination=destination,
        server_smtp=server_smtp,
        printfailedmessage=printfailedmessage,
        pdfkit_options=pdfkit_options,
        smtp_tls=smtp_tls,
        smtp_port=smtp_port,
        mail_msg_flag=mail_msg_flag,
        filter_criteria=filter_criteria,
    )
