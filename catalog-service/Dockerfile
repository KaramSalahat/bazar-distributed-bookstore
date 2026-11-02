FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py init_db.py books.json ./
EXPOSE 5001
CMD ["sh", "-c", "python init_db.py && python app.py"]
