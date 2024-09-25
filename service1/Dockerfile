FROM python:3.9-slim

RUN apt-get update && apt-get install -y procps

WORKDIR /app
COPY . .

RUN pip install flask requests
CMD ["python", "app.py"]
