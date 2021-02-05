FROM python:3.9.1-slim-buster

RUN apt-get update && \
    apt-get install -y xvfb openscad && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "/bin/bash", "/usr/src/app/entrypoint.sh" ]