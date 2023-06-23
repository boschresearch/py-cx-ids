FROM python:3

WORKDIR "/app"

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD pycxids pycxids

CMD ["python", "-m", "uvicorn", "pycxids.core.http_binding.consumer:app", "--host", "0.0.0.0", "--port", "8080"]
