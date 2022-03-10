FROM python:3.9-slim-buster

ARG TARGETARCH

COPY install_wkhtmltox.sh /build/install_wkhtmltox.sh
RUN /build/install_wkhtmltox.sh 0.12.6-1 buster $TARGETARCH
RUN rm -R /build

ENV PYTHONPATH=${PYTHONPATH}:${PWD}
RUN pip3 install poetry

RUN mkdir /app
COPY /src /app
COPY pyproject.toml /app
COPY runner.sh /app/runner.sh
RUN chmod +x /app/runner.sh
WORKDIR /app

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

ENTRYPOINT ["/app/runner.sh"]
