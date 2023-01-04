
FROM python:3.8-bullseye

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apt-get update

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

EXPOSE 8000

ENTRYPOINT ["python3"]

CMD ["-m", "uvicorn", "ui_app.main:app", "--host", "0.0.0.0"]
