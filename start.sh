#!/bin/bash
gunicorn chatterbox.asgi:application -k uvicorn.workers.UvicornWorker 