FROM python:3.5.6-stretch

COPY . /usr/src/google-mock
WORKDIR /usr/src/google-mock

RUN pip install -r requirements.txt

ENTRYPOINT [ "python" ]

EXPOSE 80

CMD [ "main.py" ]
