FROM python:3.10
WORKDIR /app
COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /app/src/streamlit
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port", "8501"]
