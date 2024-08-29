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

dynamodb_client = boto3.client('dynamodb')
CHECKPOINT_TABLE = "PDFProcessingCheckpoints"

bedrock_client = boto3.client("bedrock-runtime")
bedrock_embeddings =BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_client)

def save_checkpoint(request_id, chunk_id, status):  # Save the checkpoint status in DynamoDB
    dynamodb_client.put_item(
        TableName=CHECKPOINT_TABLE,
        Item={
            'RequestID': {'S': request_id},
            'ChunkID': {'N': str(chunk_id)},
            'Status': {'S': status}
        }
    )


def get_last_processed_chunk(request_id):    # Get the last processed chunk from DynamoDB
    response = dynamodb_client.query(
        TableName=CHECKPOINT_TABLE,
        KeyConditionExpression='RequestID = :requestid',
        ExpressionAttributeValues={
            ':requestid': {'S': request_id}
        },
        ScanIndexForward=False,
        Limit=1
    )
    
    items = response.get('Items')
    if items:
        return int(items[0]['ChunkID']['N'])
    return -1


def split_into_docs(pages, chunk_size, overlap_size):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap_size)
    documents = text_splitter.split_documents(pages)
    return documents


def create_vector_store(request_id, chunk_id, document, local_folder_path):    # Vectorize chunk and upload to S3
    chunk_embeddings = bedrock_embeddings.embed_texts([document]) 
        
    faiss_vector_store = FAISS.from_documents([document], chunk_embeddings)
    faiss_vector_store.save_local(index_name=f"{request_id}_{chunk_id}", folder_path=local_folder_path)    # Save the vector store for the chunk
    
    s3_client.upload_file(Filename=f"vs_{request_id}_{chunk_id}.faiss", Bucket=S3_BUCKET_NAME, Key=f"vs_{request_id}_{chunk_id}.faiss")
    s3_client.upload_file(Filename=f"vs_{request_id}_{chunk_id}.pkl", Bucket=S3_BUCKET_NAME, Key=f"vs_{request_id}_{chunk_id}.pkl")
    
    save_checkpoint(request_id, chunk_id, 'PROCESSED')
    streamlit.write(f"Processed Chunk:{chunk_id}, uploaded FAISS Vector Store to S3.")

    return True


def process_pdf(pdf_name, request_id):
    """Process PDF into chunks and create a vector store."""
    pdfLoader = PyPDFLoader(pdf_name)
    pages = pdfLoader.load_and_split()

    streamlit.write(f"Total # of Pages: {len(pages)}")

    last_processed_chunk = get_last_processed_chunk(request_id)
    start_chunk = last_processed_chunk + 1

    documents = split_into_docs(pages, 1000, 200)
    streamlit.write("Finished processing pages into documents.\n\n")

    local_folder_path = "/vector_stores/"
    os.makedirs(local_folder_path, exist_ok=True)

    for chunk_id in range(start_chunk, len(documents)):
        document = documents[chunk_id]
        result = create_vector_store(request_id, chunk_id, document, local_folder_path)
        if not result:
            streamlit.write(f"Failed to create Vector Store for Chunk:{chunk_id}. Please check the logs.")
            break


def main():
    streamlit.write("Hi, Welcome to the Admin's Page!")
    uploaded_pdf = streamlit.file_uploader("Choose file to upload", "pdf")
    if uploaded_pdf:
        request_id = f"admin_{str(uuid.uuid4())}"
        streamlit.write(f"Request ID: {request_id}")
        saved_file_name = f"{request_id}.pdf"
        with open(saved_file_name, "wb") as sf:
            sf.write(uploaded_pdf.getvalue())

        process_pdf(saved_file_name, request_id)


if __name__ == "__main__":
    main()