import boto3
import streamlit
import uuid
import os

from langchain_community.embeddings import BedrockEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


s3_client = boto3.client("s3")
S3_BUCKET_NAME = "gen-ai-pdf-interaction"

def main():
    streamlit.write("Hi, Welcome to the Admin's Page!")
    uploaded_pdf = streamlit.file_uploader("Choose file to upload", "pdf")
    if uploaded_pdf:
        request_id = str(uuid.uuid4())
        streamlit.write(f"Request ID: {request_id}")
        saved_file_name = f"{request_id}.pdf"
        with open(saved_file_name, "wb") as sf:
            sf.write(uploaded_pdf.getvalue())

        pdfLoader = PyPDFLoader(saved_file_name)
        pages = pdfLoader.load_and_split()

        streamlit.write(f"Total # of Pages: {len(pages)}")


if __name__ == "__main__":
    main()