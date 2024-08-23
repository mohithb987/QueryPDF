FROM python:3.12
EXPOSE 8083
WORKDIR /app

COPY . ./

RUN pip install -r requirements.txt
ENTRYPOINT [ "streamlit", "run", "admin.py", "--server.port=8083", "--server.address=0.0.0.0" ]