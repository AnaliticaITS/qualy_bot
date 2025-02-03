FROM python:3.11.9
LABEL maintainer=andres_munhoz

WORKDIR /bot

COPY . .

RUN pip install --no-cache-dir --upgrade -r /bot/requirements.txt

RUN mkdir -p /bot/downloads

CMD ["python", "qualy.py"]