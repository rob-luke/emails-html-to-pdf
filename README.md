# Email to PDF to email

This script will check an imap folder for unread emails.
Any unread email that does not have an attachment will be converted to a pdf
and then emailed to the address you specify.
The script is run at a configurable interval.

This was built to integrate with [paperless-ng](https://github.com/jonaswinkler/paperless-ng) 
which works with pdf attachements.
However, I get many documents that are html only, so I wanted them converted
to pdf for storage in paperless-ng.


## Usage

The following parameters are used (defaults in parentheses):

* `IMAP_URL` 
* `IMAP_USERNAME`
* `IMAP_PASSWORD`
* `IMAP_FOLDER` Which folder to watch for unread emails
* `SMTP_URL`
* `MAIL_SENDER`: Address the mail with pdf should be sent from
* `MAIL_DESTINATION`: Where to send the resulting pdf
* `SMTP_PORT`: (587)
* `SMTP_TLS`: (True)
* `INTER_RUN_INTERVAL`: Time in seconds that the system should wait between running the script
* `PRINT_FAILED_MSG`: Flag to control printing of error messages
* `HOSTS`: [Semicolon separated list of hosts](https://github.com/rob-luke/emails-html-to-pdf/pull/12) that should be added to /etc/hosts to prevent dns lookup failures 
* `WKHTMLTOPDF_OPTIONS`: Python dict (json) representation of wkhtmltopdf_options that can be passed to the used pdfkit library
* `MAIL_MESSAGE_FLAG`: Flag to apply to email after processing.  
    Must be one of [imap-tools flags](https://github.com/ikvk/imap_tools/blob/7f8fd5e4f3976bbd2efa507843c577affa61d996/imap_tools/consts.py#L10). Values: SEEN (default), ANSWERED, FLAGGED, DELETED, DRAFT, RECENT

### Docker-Compose

#### 1. Use prebuilt image

This image is stored in the github registry, so you can use it without downloading this code repository.
The image address is `ghcr.io/rob-luke/emails-html-to-pdf:latest`.
So to use it in a docker-compose it would be something like...

```yaml
version: "3.8"

services:

  email2pdf:
    image: ghcr.io/rob-luke/emails-html-to-pdf:latest
    container_name: email2pdf
    environment:
      - IMAP_URL=imap.provider.com
      - IMAP_USERNAME=user@provider.net
      - IMAP_PASSWORD=randompassword
      - IMAP_FOLDER=Paperless
      - SMTP_URL=smtp.provider.com
      - MAIL_SENDER=user+paperless@provider.net
      - MAIL_DESTINATION=user+paperless@provider.net
      - INTER_RUN_INTERVAL=600
      - HOSTS=127.0.0.1 tracking.paypal.com
      - WKHTMLTOPDF_OPTIONS={"load-media-error-handling":"ignore"}
```


#### 2. Build image yourself

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

## Hints

### Possible Errors

#### PayPal Mail with HostNotFoundErrors
* try adding `127.0.0.1 tracking.paypal.com` to the `HOSTS` env (check for missing domain in error log)
* add `{"load-media-error-handling":"ignore"}` as `WKHTMLTOPDF_OPTIONS` option (could be the tracking pixel that is not beeing loaded
* append `"enable-local-file-access":true` or `"load-error-handling":"ignore"`to `WKHTMLTOPDF_OPTIONS` if you get a `file://...` error
* add `127.0.0.1 true` to the `HOSTS` env if you get a `http:///true/...` error

## Development

The recommended editor for development is either IntelliJ or Visual Studio Code

### Visual Studio Code

For Visual Studio Code, it is recommended to use the devcontainer included in the repository. With the
[Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
extension installed, you should be prompted to open the devcontainer when opening the folder.

For debugging, copy the `env.example` file and rename it to just `env`. Then edit the variables inside
to the required values for testing. These will be automatically configured when launching via either the
debug menu or by pressing F5. The `env` file is included in the gitignore.

Formatting issues will cause the github build to fail. To fix formatting issues in your script, open the file
and run the "Format Document" command.