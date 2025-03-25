FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=user_service.py
ENV FLASK_ENV=development

EXPOSE 5003

CMD ["python", "user_service.py"] 