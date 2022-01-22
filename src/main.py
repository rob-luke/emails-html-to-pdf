#!/usr/bin/env python

import logging
from filenameutils import replace_bad_chars, replace_unpleasant_chars
from outputs import OutputToFolder, SendOutputByEmail
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
    mail_msg_flag=None,
    failed_messages_threshold=3,
):
    logging.info("Starting mail processing run")
    if printfailedmessage:
        logging.warning("*On failure, the Body of the email will be printed*")

    PDF_CONTENT_ERRORS = [
        "ContentNotFoundError",
        "ContentOperationNotPermittedError",
        "UnknownContentError",
        "RemoteHostClosedError",
        "ConnectionRefusedError",
        "Server refused a stream",
    ]

    failed_messages = 0

    with MailBox(imap_url).login(imap_username, imap_password, imap_folder) as mailbox:
        for i, msg in enumerate(
            mailbox.fetch(
                criteria=AND(seen=False),
                limit=num_emails_limit,
                mark_seen=False,
            )
        ):
            try:
                if len(msg.attachments) != 0:
                    logging.warning(
                        f"Attachments found in {msg.subject}. Messages with attachments cannot be converted to PDF. Skipping."
                    )
                    continue

                if not msg.html.strip() == "":  # handle text only emails
                    logging.debug(f"Message '{msg.subject}' is HTML")
                    pdftext = (
                        '<meta http-equiv="Content-type" content="text/html; charset=utf-8"/>'
                        + msg.html
                    )
                else:
                    logging.debug(f"Message '{msg.subject}' is plain text")
                    pdftext = msg.text

                filename = replace_bad_chars(replace_unpleasant_chars(msg.subject))
                filename = f"{filename[:50]}.pdf"
                logging.debug(f"Using '{filename}' for PDF filename")

                logging.info(f"Exporting message '{msg.subject}' to PDF")
                options = {}
                if pdfkit_options is not None:
                    # parse WKHTMLTOPDF Options to dict
                    options = json.loads(pdfkit_options)
                try:
                    pdfkit.from_string(pdftext, filename, options=options)
                except OSError as e:
                    outputMessage = ""
                    if any([error in str(e) for error in PDF_CONTENT_ERRORS]):
                        # allow pdfs with missing images if file got created
                        if os.path.exists(filename):
                            if printfailedmessage:
                                outputMessage += f"\n{pdftext}\n"
                            outputMessage += f"\n **** HANDLED EXCEPTION ****"
                            outputMessage += f"\n\n{str(e)}\n"
                            outputMessage += f"\nOne or more remote resources failed to load, continuing without them."
                            logging.warning(outputMessage)

                        else:
                            if printfailedmessage:
                                outputMessage += f"\n{pdftext}\n"
                            outputMessage += f"\n !!!! UNHANDLED EXCEPTION with PDF Content Errors: {PDF_CONTENT_ERRORS} !!!!"
                            outputMessage += f"\n{str(e)}"
                            logging.error(outputMessage)
                            raise e
                    else:
                        if printfailedmessage:
                            outputMessage += f"\n{pdftext}\n"
                        outputMessage += f"\n !!!! UNHANDLED EXCEPTION !!!!"
                        outputMessage += f"\n{str(e)}"
                        logging.error(outputMessage)
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
                        logging.warning(
                            f"Unrecognised message flag '{mail_msg_flag}'. Using 'SEEN' instead."
                        )
                        flag = MailMessageFlags.SEEN
                    logging.info(f"Marking processed message as '{mail_msg_flag}'")
                    mailbox.flag(msg.uid, flag, True)

                logging.debug(f"Deleting processed PDF '{filename}'...")
                os.remove(filename)
                logging.info(f"Finished processing of message '{msg.subject}'")
            except Exception as e:
                logging.exception(str(e))
                failed_messages += 1

                if failed_messages >= failed_messages_threshold:
                    errorMessage = f"The number of errors has reached the failed messages threshold. Processing will be halted. Please resolve issues before resuming."
                    logging.critical(errorMessage)
                    raise RuntimeError(errorMessage)

                logging.info("Continuing with next message")

    if failed_messages > 0:
        logging.warn("Completed mail processing run with one or more errors")
    else:
        logging.info("Completed mail processing run")


if __name__ == "__main__":

    log_level = os.environ.get("LOG_LEVEL", "INFO")
    if log_level == "DEBUG":
        log_level = logging.DEBUG
    elif log_level == "INFO":
        log_level = logging.INFO
    elif log_level == "WARNING":
        log_level = logging.WARNING
    elif log_level == "ERROR":
        log_level = logging.ERROR
    else:
        logging.warning(
            f"Unrecognised logging level '{log_level}'. Defaulting to INFO level."
        )
        log_level = logging.INFO
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=log_level
    )

    server_imap = os.environ.get("IMAP_URL")
    imap_username = os.environ.get("IMAP_USERNAME")
    imap_password = os.environ.get("IMAP_PASSWORD")
    folder = os.environ.get("IMAP_FOLDER")

    output_type = os.getenv("OUTPUT_TYPE", "mailto")

    printfailedmessage = os.getenv("PRINT_FAILED_MSG", "False") == "True"
    pdfkit_options = os.environ.get("WKHTMLTOPDF_OPTIONS")
    mail_msg_flag = os.environ.get("MAIL_MESSAGE_FLAG")

    output = None
    if output_type == "mailto":
        server_smtp = os.environ.get("SMTP_SERVER")
        smtp_username = os.environ.get("SMTP_USERNAME", imap_username)
        smtp_password = os.environ.get("SMTP_PASSWORD", imap_password)
        sender = os.environ.get("MAIL_SENDER", smtp_username)
        destination = os.environ.get("MAIL_DESTINATION")
        smtp_port = os.environ.get("SMTP_PORT", 587)
        smtp_encryption = os.environ.get(
            "SMTP_ENCRYPTION", SendOutputByEmail.SMTP_ENCRYPTION_STARTTLS
        )
        output = SendOutputByEmail(
            sender,
            destination,
            server_smtp,
            smtp_port,
            smtp_username,
            smtp_password,
            smtp_encryption,
        )
    elif output_type == "folder":
        output_folder = os.getenv("OUTPUT_FOLDER")
        output = OutputToFolder(output_folder)

    if not output:
        raise ValueError(f"Unknown output type '{output_type}'")

    logging.info("Running emails-html-to-pdf")

    with output:
        process_mail(
            output=output,
            imap_url=server_imap,
            imap_username=imap_username,
            imap_password=imap_password,
            imap_folder=folder,
            printfailedmessage=printfailedmessage,
            pdfkit_options=pdfkit_options,
            mail_msg_flag=mail_msg_flag,
        )
