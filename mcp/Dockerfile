FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY requirements.txt .
RUN uv venv
RUN uv pip install -r requirements.txt

COPY client.py .

CMD ["uv", "run", "client.py"]


