FROM python:3.10

# Fastapi deployment
# https://fastapi.tiangolo.com/deployment/docker/

WORKDIR /code

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY *.py ./

CMD ["python", "./main.py"]
