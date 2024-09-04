import boto3
import streamlit
import uuid
import os

from langchain_aws.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

s3_client            = boto3.client("s3")
S3_BUCKET_NAME       = "gen-ai-pdf-interaction"
download_folder_path = "/tmp"
bedrock_client       = boto3.client("bedrock-runtime")
bedrock_embeddings   = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_client)


def get_llm():
    llm = Bedrock(
            model_id="anthropic.claude-v2:1", 
            client=bedrock_client,
            model_kwargs={'max_tokens_to_sample': 512}
        )
    
    return llm


def get_response(llm, vector_store, question):
    prompt_template = """
    
    Human: Please use the given context and provide a concise answer to the question below. If you do not know the answer, respond that the answer is not known and do not try to make up an answer.

    <context>
    {context}
    </context>

    Question: {question}

    Assistant:
    """

    prompt = PromptTemplate(
                template=prompt_template, 
                input_variables=["context","question"]
            )

    qa = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5}),
                        return_source_documents=True,
                        chain_type_kwargs={"prompt": prompt}
                        )

    answer = qa({"query": question})

    return answer['result']

def load_index():
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
    if 'Contents' in response and len(response['Contents']) > 0:
        for content in response['Contents']:
            key = content['Key']
            s3_client.download_file(Bucket=S3_BUCKET_NAME, Key=key, Filename=f"{download_folder_path}/{key}")
            print(f'Downloaded {key} to {download_folder_path}/{key}')
    else:
        print('No objects were found in the S3 bucket.')



def main():
    streamlit.header("GenAI-PDFInteraction App")
    streamlit.write('##')
    streamlit.write("Hi, welcome to the homepage.")
    
    load_index()

    files_list = os.listdir(download_folder_path)
    streamlit.write("##")
    streamlit.write(f"List of files in {download_folder_path}:")
    streamlit.write(files_list)
    streamlit.write("###")
    
    for idx, f in enumerate(files_list):
        streamlit.write(f"File {idx}: {f}")
        if f.endswith(".faiss"):
            faiss_index_name=f.removesuffix(".faiss")

    faiss_index = FAISS.load_local(
                            index_name=faiss_index_name, 
                            folder_path=download_folder_path, 
                            embeddings=bedrock_embeddings,
                            allow_dangerous_deserialization=True
                        )

    streamlit.write("##")
    streamlit.write(f"Created Index from '{faiss_index_name}'.")
    streamlit.write("##")
    
    question = streamlit.text_input("Please enter your question.")
    if streamlit.button("Ask"):
        with streamlit.spinner("Querying..."):
            llm = get_llm()
            response = get_response(llm, faiss_index, question)
            streamlit.write(response)
            streamlit.success("Done")


if __name__ == "__main__":
    main()