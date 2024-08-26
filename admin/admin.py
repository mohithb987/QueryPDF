import boto3
import streamlit
import uuid
import os

from langchain_aws.embeddings import BedrockEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS


s3_client = boto3.client("s3")
S3_BUCKET_NAME = "gen-ai-pdf-interaction"
bedrock_client = boto3.client("bedrock-runtime")
bedrock_embeddings =BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_client)


def split_into_docs(pages, chunk_size, overlap_size):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap_size)
    documents = text_splitter.split_documents(pages)
    return documents


def create_vector_store(request_id, documents):
    faiss_vector_store = FAISS.from_documents(documents, bedrock_embeddings)
    folder_path = "/vector_stores/"
    file_name = f"{request_id}.bin"
    faiss_vector_store.save_local(index_name=file_name, folder_path=folder_path)
    
    s3_client.upload_file(Filename = folder_path+file_name+".faiss", Bucket=S3_BUCKET_NAME, Key=f"vs_{request_id}.faiss")
    s3_client.upload_file(Filename = folder_path+file_name+".pkl", Bucket=S3_BUCKET_NAME, Key=f"vs_{request_id}.pkl")
    return True


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

        documents = split_into_docs(pages, 1000, 200)

        streamlit.write(f'Split Docs length: {len(documents)}')
        streamlit.write("\n\n------------------------\n\n")
        streamlit.write("Sample Doc 0:\n\n")
        streamlit.write(documents[0])
        streamlit.write("\n\n------------------------\n\n")    
        streamlit.write("\n\nSample Doc 1:\n\n")
        streamlit.write(documents[1])
        streamlit.write("\n\n------------------------")

        streamlit.write("Finished processing pages into documents.\n\n")
        
        streamlit.write("Creating the Vector Store using FAISS ...")
        result = create_vector_store(request_id, documents)
        if result:
            streamlit.write("Vector Store creation successful.")
        else:
             streamlit.write("Failed to create Vector Store. Please check the logs.")


if __name__ == "__main__":
    main()