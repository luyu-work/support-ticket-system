FROM python:3.12-slim

WORKDIR /application

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:ticket_system_application", "--host", "0.0.0.0", "--port", "8000"]
