FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=order_service.py
ENV FLASK_ENV=development

CMD ["python", "order_service.py"] 