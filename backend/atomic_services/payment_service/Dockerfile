FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=payment_service.py
ENV FLASK_ENV=development

EXPOSE 8002

# CMD ["flask", "run", "--host=0.0.0.0"] 
CMD ["python", "payment_service.py"]