import streamlit as st
import boto3
from botocore.exceptions import ClientError
import configparser

def init_cognito_client(region_name, client_id):
    return boto3.client('cognito-idp', region_name=region_name)

def authenticate_user(client, client_id, username, password):
    try:
        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        return response
    except ClientError as e:
        st.error(f"Authentication failed: {e}")
        return None

def redirect_to(url):
    st.markdown(f'<meta http-equiv="refresh" content="0; url={url}">', unsafe_allow_html=True)

def fetch_alb_url(tag_key, tag_value):
    client = boto3.client('elbv2')
    try:
        response = client.describe_load_balancers()
        for lb in response['LoadBalancers']:
            lb_arn = lb['LoadBalancerArn']
            lb_tags = client.describe_tags(ResourceArns=[lb_arn])
            tags = lb_tags['TagDescriptions'][0]['Tags']
            for tag in tags:
                if tag['Key'] == tag_key and tag['Value'] == tag_value:
                    return lb['DNSName']
    except ClientError as e:
        st.error(f"Failed to fetch ALB URL: {e}")
    return None

config = configparser.ConfigParser()
config.read('../credentials.conf')

REGION_NAME = config.get('aws', 'region')
ADMIN_USER_POOL_ID = config.get('aws', 'admin_user_pool_id')
ADMIN_CLIENT_ID = config.get('aws', 'admin_app_client_id')
USER_USER_POOL_ID = config.get('aws', 'user_user_pool_id')
USER_CLIENT_ID = config.get('aws', 'user_app_client_id')

alb_tag_key = config.get('alb_tag_key')
alb_tag_value =config.get('alb_tag_value')
ALB_URL = fetch_alb_url(alb_tag_key, alb_tag_value)

if st.button("Login as Admin"):
    st.session_state.page = 'admin_login'
elif st.button("Login as User"):
    st.session_state.page = 'user_login'

if 'page' in st.session_state:
    if st.session_state.page == 'admin_login':
        st.header("Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            client = init_cognito_client(REGION_NAME, ADMIN_CLIENT_ID)
            response = authenticate_user(client, ADMIN_USER_POOL_ID, ADMIN_CLIENT_ID, username, password)
            if response and ALB_URL:
                redirect_to(f"https://{ALB_URL}/admin")

    elif st.session_state.page == 'user_login':
        st.header("User Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            client = init_cognito_client(REGION_NAME, USER_CLIENT_ID)
            response = authenticate_user(client, USER_USER_POOL_ID, USER_CLIENT_ID, username, password)
            if response and ALB_URL:
                redirect_to(f"https://{ALB_URL}/user")