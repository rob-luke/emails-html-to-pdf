# Email to PDF to email

This script will check an imap folder for unread emails.
Any unread email that does not have an attachment will be converted to a pdf
and then emailed back to that account.

This was built to integrate with paperless-ng which works with pdf attachements.
However, I get many bills that are html only, so I wanted them converted
to pdf for storage in paperless-ng.


## Usage

The following parameters are used:

* `IMAP_URL` 
* `IMAP_USERNAME`
* `IMAP_PASSWORD`
* `IMAP_FOLDER` Which folder to watch for unread emails
* `SMTP_URL`
* `MAIL_SENDER`: Address the mail with pdf should be sent from
* `MAIL_DESTINATION`: Where to send the resulting pdf

### Docker

Open the docker-compose file and enter your details in the environment.
This will run the script every minute.


```bash
docker-compose up -d
```

### Python

Or if you prefer you can run the script manually by running these commands.

```bash
poetry install
poetry run src/main.py
```
