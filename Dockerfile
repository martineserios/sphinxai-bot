FROM python:3.7

RUN /usr/local/bin/python -m pip install --upgrade pip

COPY requirements.txt /
RUN pip install -r requirements.txt

COPY src/ app/src/
COPY temp_media/ /app
COPY client_secret.json /app
WORKDIR /app

ENV PORT 8080
ENV TOKEN 1739358107:AAHLRPqza2PmSu1oW8hdnpCZWhmerXXu7YE

ENTRYPOINT [ "/bin/bash", "-l", "-c" ]
CMD [ "python3", "bot.py" ]