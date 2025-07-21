# Mostly just following the steps at https://hub.docker.com/_/python/
# Adapting only as needed
FROM docker.io/python:3.13-slim

WORKDIR /usr/src/app

# Install dependencies using frozen to avoid breakages from updates
COPY frozen-requirements.txt ./
RUN pip install --no-cache-dir -r frozen-requirements.txt

# Copying just the two files I need
COPY Poller Poller/
COPY Teller Teller/
# To mount a directory to contain polls, mount a folder to
# /usr/src/app/Poller/polls

# Setting the teller location absolutely to avoid issues then CDing to Poller
ENV TELLER_LOCATION="/usr/src/app/Teller/main.py"
WORKDIR Poller

# Allow proxies to communicate from any address
# As this is meant to run behind a reverse proxy
# Change this if you're not doing this
CMD [ "uvicorn" "main:app" "--forwarded-allow-ips" "*" ]
