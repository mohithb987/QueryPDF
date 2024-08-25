FROM python:3.11
EXPOSE 8084
WORKDIR /app

COPY . ./

RUN pip install -r requirements.txt
ENTRYPOINT [ "streamlit", "run", "app.py", "--server.port=8084", "--server.address=0.0.0.0" ]