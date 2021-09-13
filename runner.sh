#!/bin/bash

while poetry run /app/main.py; do sleep 60; done
