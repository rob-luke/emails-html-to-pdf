#!/bin/bash

echo ${INTER_RUN_INTERVAL}

while poetry run /app/main.py; do sleep ${INTER_RUN_INTERVAL}; done
