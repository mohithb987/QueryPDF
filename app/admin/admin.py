import boto3
import streamlit
import uuid
import os
import time
import threading

from langchain_aws.embeddings import BedrockEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS


# Hard-coded items
CHECKPOINT_TABLE = "PDFProcessingCheckpoints"
HEARTBEAT_TABLE = "ContainerHeartbeats"
CONTAINER_INFO_TABLE = "ContainerInfo"
HEARTBEAT_INTERVAL = 60

# Environment Variables
admin_name = os.getenv("CONSUMER_NAME")
container_id = os.getenv("CONTAINER_ID")
az = os.getenv("AVAILABILITY_ZONE")

s3_client = boto3.client("s3")
dynamodb_client = boto3.client("dynamodb")
bedrock_client = boto3.client("bedrock-runtime")
bedrock_embeddings =BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_client)


def save_container_info(admin_name, container_id, role, az):
    """ Saves Container Info to a DynamoDB Table"""
    dynamodb_client.put_item(
        TableName=CONTAINER_INFO_TABLE,
        Item={
            'AdminName': {'S': admin_name},
            'ContainerID': {'S': container_id},
            'Role': {'S': role},
            'AZ': {'S': az}
        }
    )


def save_checkpoint(request_id, chunk_id, status):
    """ Saves Checkpointing Info to a DynamoDB Table to help resume any failed operations """
    dynamodb_client.put_item(
        TableName=CHECKPOINT_TABLE,
        Item={
            'RequestID': {'S': request_id},
            'ChunkID': {'N': str(chunk_id)},
            'Status': {'S': status}
        }
    )


def save_heartbeat(container_id, request_id):
    """ Periodically Sends Container Heartbeats to help identify when a container goes down """
    while True:
        timestamp = int(time.time())
        dynamodb_client.put_item(
            TableName=HEARTBEAT_TABLE,
            Item={
                'ContainerID': {'S': container_id},
                'RequestID': {'S': request_id},
                'Timestamp': {'S': str(timestamp)},
                'Health': {'S': "OK"}
            }
        )
        time.sleep(HEARTBEAT_INTERVAL)


def get_last_processed_chunk(request_id):
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


def create_vector_store(request_id, chunk_id, document, local_folder_path):
    chunk_embeddings = bedrock_embeddings.embed_texts([document]) 
        
    faiss_vector_store = FAISS.from_documents([document], chunk_embeddings)
    faiss_vector_store.save_local(index_name=f"{request_id}_{chunk_id}", folder_path=local_folder_path)
    
    s3_bucket_name = f"GPI-{request_id}"
    s3_client.create_bucket(Bucket=s3_bucket_name)
    
    s3_client.upload_file(Filename=f"vs_{request_id}_{chunk_id}.faiss", Bucket=s3_bucket_name, Key=f"vs_{request_id}_{chunk_id}.faiss")
    s3_client.upload_file(Filename=f"vs_{request_id}_{chunk_id}.pkl", Bucket=s3_bucket_name, Key=f"vs_{request_id}_{chunk_id}.pkl")
    
    save_checkpoint(request_id, chunk_id, 'PROCESSED')
    streamlit.write(f"Processed Chunk:{chunk_id}, uploaded FAISS Vector Store to S3 bucket: {s3_bucket_name}.")

    return True


def process_pdf(pdf_name, request_id):
    """Process PDF into chunks and create a vector store."""
    pdfLoader = PyPDFLoader(pdf_name)
    pages = pdfLoader.load_and_split()

    streamlit.write(f"Total # of Pages: {len(pages)}")

    documents = split_into_docs(pages, 1000, 200)
    streamlit.write("Finished processing pages into documents.\n\n")

    last_processed_chunk = get_last_processed_chunk(request_id)
    start_chunk = last_processed_chunk + 1

    local_folder_path = "/vector_stores/"
    os.makedirs(local_folder_path, exist_ok=True)

    for chunk_id in range(start_chunk, len(documents)):
        document = documents[chunk_id]
        result = create_vector_store(request_id, chunk_id, document, local_folder_path)
        if not result:
            streamlit.write(f"Failed to create Vector Store for Chunk:{chunk_id}. Please check the logs.")
            break


def get_failed_requests():
    response = dynamodb_client.scan(
        TableName=CHECKPOINT_TABLE,
        FilterExpression='Status = :status',
        ExpressionAttributeValues={':status': {'S': 'FAILED'}}
    )
    
    failed_requests = response.get('Items', [])
    failed_request_ids = [req['RequestID']['S'] for req in failed_requests]

    return failed_request_ids


def main():
    save_container_info(admin_name=admin_name, container_id=container_id, role="admin",  az=az)
    streamlit.write("Hi, Welcome to the Admin's Page!")

    heartbeat_thread = threading.Thread(target=save_heartbeat, args=(container_id, request_id))
    heartbeat_thread.daemon = True
    heartbeat_thread.start()

    uploaded_pdf = streamlit.file_uploader("Choose file to upload", "pdf")
    if uploaded_pdf:
        pdf_name = streamlit.text_input("Enter PDF name (without spaces):")
        if pdf_name:
            if ' ' in pdf_name:
                streamlit.write("PDF name should not contain spaces.")
            else:
                request_id = f"{pdf_name}"
                s3_bucket_name = f"GPI-{request_id}"
                
                s3_response = s3_client.list_objects_v2(Bucket=s3_bucket_name, Prefix=f"{request_id}.pdf")
                if 'Contents' in s3_response:
                    streamlit.write(f"A PDF with the name '{pdf_name}' already exists in the bucket '{s3_bucket_name}'. Please choose a different name.")
                else:
                    streamlit.write(f"Request ID: {request_id}")
                    saved_file_name = f"{request_id}.pdf"
                    with open(saved_file_name, "wb") as sf:
                        sf.write(uploaded_pdf.getvalue())
                    
                    s3_client.upload_file(Filename=saved_file_name, Bucket=s3_bucket_name, Key=f"{request_id}.pdf")
                    process_pdf(saved_file_name, request_id)

    if uploaded_pdf is None:
        streamlit.write("If any of your previous processings were failed and you want to resume, select from the list below:")
        failed_requests = get_failed_requests()
        selected_request_id = streamlit.selectbox("Select a Request ID to resume:", ["Select an ID"] + failed_requests)

        if selected_request_id != "Select an ID":
            streamlit.write(f"Resuming processing for Request ID: {selected_request_id}")
            saved_file_name = f"{selected_request_id}.pdf"
            process_pdf(saved_file_name, selected_request_id)


if __name__ == "__main__":
    main()