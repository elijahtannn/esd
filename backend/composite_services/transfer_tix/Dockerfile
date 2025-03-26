FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_APP=transfer.py
ENV FLASK_ENV=development

EXPOSE 8011

CMD ["python", "transfer.py"] 