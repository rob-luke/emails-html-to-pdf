#!/usr/bin/env python

from outputs import SendOutputByEmail
import pdfkit
import json
from imap_tools import MailBox, AND, MailMessageFlags
import os


def process_mail(
    output,
    mark_msg=True,
    num_emails_limit=50,
    imap_url=None,
    imap_username=None,
    imap_password=None,
    imap_folder=None,
    printfailedmessage=None,
    pdfkit_options=None,
    mail_msg_flag=None
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
                criteria=AND(seen=False),
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

                output.process(msg, [filename])

                if mark_msg:
                    flag = None
                    if mail_msg_flag == "SEEN":
                        flag = MailMessageFlags.SEEN
                    elif mail_msg_flag == "ANSWERED":
                        flag = MailMessageFlags.ANSWERED
                    elif mail_msg_flag == "FLAGGED":
                        flag = MailMessageFlags.FLAGGED
                    elif mail_msg_flag == "DELETED":
                        flag = MailMessageFlags.DELETED
                    elif mail_msg_flag == "DRAFT":
                        flag = MailMessageFlags.DRAFT
                    elif mail_msg_flag == "RECENT":
                        flag = MailMessageFlags.RECENT
                    else:
                        flag = MailMessageFlags.SEEN
                    mailbox.flag(msg.uid, flag, True)
                os.remove(filename)
    print("Completed mail processing run\n\n", flush=True)


if __name__ == "__main__":

    server_imap = os.environ.get("IMAP_URL")
    username = os.environ.get("IMAP_USERNAME")
    password = os.environ.get("IMAP_PASSWORD")
    folder = os.environ.get("IMAP_FOLDER")

    output_type = os.getenv('OUTPUT_TYPE', 'mailto')

    server_smtp = os.environ.get("SMTP_URL")
    sender = os.environ.get("MAIL_SENDER")
    destination = os.environ.get("MAIL_DESTINATION")
    smtp_port = os.getenv("SMTP_PORT", 587)
    smtp_tls = os.getenv("SMTP_TLS", True)

    printfailedmessage = os.getenv("PRINT_FAILED_MSG", "False") == "True"
    pdfkit_options = os.environ.get("WKHTMLTOPDF_OPTIONS")
    mail_msg_flag = os.environ.get("MAIL_MESSAGE_FLAG")

    output=None
    if output_type == 'mailto':
        output=SendOutputByEmail(sender, destination, server_smtp, smtp_port, username, password, smtp_tls)

    if not output:
        raise ValueError("Unknown output type '{output_type}'")

    print("Running emails-html-to-pdf")

    with output:
        process_mail(
            output=output,
            imap_url=server_imap,
            imap_username=username,
            imap_password=password,
            imap_folder=folder,
            printfailedmessage=printfailedmessage,
            pdfkit_options=pdfkit_options,
            mail_msg_flag=mail_msg_flag
        )
