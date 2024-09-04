import uuid
import boto3
from aws_resource_fetcher import AWSResourceFetcher
import re
import json
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

resource_fetcher = AWSResourceFetcher()
container_info_table = resource_fetcher.get_dynamodb_table(table_name="ContainerInfo")
subnets = resource_fetcher.get_subnets()

ecs_client = boto3.client('ecs')
dynamodb = boto3.resource('dynamodb')
autoscaling_client = boto3.client('application-autoscaling')


def generate_unique_container_id():
    while True:
        container_id = str(uuid.uuid4())
        response = container_info_table.get_item(Key={'ContainerID': container_id})
        if 'Item' not in response:
            logger.info(f'Generated Container ID: {container_id}')
            return container_id


def create_or_update_ecs_service(consumer_name, role, image, az):
    """ Adds container to an existing service, or creates new service with a container """
    try:
        # Common Tags
        tags = [
            {"key": "Application", "value": "GPI-App"},
            {"key": "Environment", "value": "Development"},
            {"key": "Owner", "value": "Mohith"},
            {"key": "Name", "value": f"GPI-ECS-{consumer_name}"} # ECS Container Name
        ]

        cluster_name     = resource_fetcher.get_ecs_cluster()
        az_suffix = az.split('-')[-1]
        ecs_service_name = f"{role}-service-{az_suffix}"

        # Subnet in which the Service should be created
        subnet_id = None
        for subnet in subnets:
            if subnet.get('AvailabilityZone') == az:
                tags = subnet.get('Tags', [])
                tag_dict = {tag['Key']: tag['Value'] for tag in tags}
                name_tag_value = tag_dict.get('Name', '')
                if re.match('GPI-private-subnet', name_tag_value):
                    subnet_id = subnet['SubnetId']

        
        logger.info(f'Creating Service: {ecs_service_name} in ECS Cluster: {cluster_name},  Subnet ID: {subnet_id}')
        
        environment = [
                        {'name': 'CONSUMER_NAME', 'value': consumer_name},
                        {'name': 'ROLE', 'value': role},
                        {'name': 'CONTAINER_ID', 'value': container_id},
                        {'name': 'AVAILABILITY_ZONE', 'value': az}
                      ]
        existing_services = ecs_client.list_services(
            cluster=cluster_name,
            maxResults=100
        )
        service_exists = any(service.endswith(ecs_service_name) for service in existing_services['serviceArns'])
        
        # Create new Service if it's not running already
        if not service_exists:
            logger.info(f'{ecs_service_name} does not exist. Creating it...')
            ecs_client.create_service(
                cluster=cluster_name,
                serviceName=ecs_service_name,
                taskDefinition=image,
                desiredCount=1,
                environment_variables=environment_variables,
                launchType='FARGATE',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': [subnet_id],
                        'assignPublicIp': 'DISABLED'
                    }
                },
                loadBalancers=[{
                    'targetGroupArn': resource_fetcher.get_target_group_arn(f'GPI-target-group-{role}'),
                    'containerName': consumer_name,
                    'containerPort': 8501
                }],
                environment=environment,
                tags=tags
            )

            logger.info(f'Finished creating {ecs_service_name}.')

            autoscaling_client.register_scalable_target(
                ServiceNamespace='ecs',
                ResourceId=f'service/{resource_fetcher.get_ecs_cluster()}/{ecs_service_name}',
                ScalableDimension='ecs:service:DesiredCount',
                MinCapacity=1,
                MaxCapacity=10,
                RoleARN=resource_fetcher.get_iam_role_arn('GPI-ECS-autoscaling-role')
            )

            autoscaling_client.put_scaling_policy(
                PolicyName='cpu-scaling-policy',
                ServiceNamespace='ecs',
                ResourceId=f'service/{resource_fetcher.get_ecs_cluster()}/{ecs_service_name}',
                ScalableDimension='ecs:service:DesiredCount',
                PolicyType='TargetTrackingScaling',
                TargetTrackingScalingPolicyConfiguration={
                    'TargetValue': 50.0,
                    'PredefinedMetricSpecification': {
                        'PredefinedMetricType': 'ECSServiceAverageCPUUtilization',
                    },
                    'ScaleInCooldown': 300,
                    'ScaleOutCooldown': 300
                }
            )
        else:
            logger.info(f'{ecs_service_name} exists already.')
            service_description = ecs_client.describe_services(
                cluster=cluster_name,
                services=[ecs_service_name]
            )
            current_desired_count = service_description['services'][0]['desiredCount']
            
            ecs_client.update_service(
                cluster=cluster_name,
                service=ecs_service_name,
                desiredCount=current_desired_count + 1
            )
            
        container_id = generate_unique_container_id()
        logger.info(f'Finished adding new container to {ecs_service_name}. Container ID: {container_id}')

        return {
            'statusCode': 200,
            'body': json.dumps(f"ECS service handled for {role}: {consumer_name}, Container ID: {container_id}")
        }

    except Exception as e:
        logger.info(f'Failed to handle ECS service.')
        return {
            'statusCode': 500,
            'body': json.dumps(f"Failed to handle ECS service: {str(e)}")
        }


def lambda_handler(event, context):
    logger.info(' --- From Lambda Function ---')
    path = event.get('path', '')
    consumer_name = path.split('/')[2] if len(path.split('/')) > 2 else None
    
    if path.startswith('/admin/'):
        role = 'admin'
        image = "admin-service"
    
    elif path.startswith('/user/'):
        role = 'user'
        image = "user-service"
    
    else:
        logger.info(f'{path} is invalid.')
        return {
            'statusCode': 400,
            'body': json.dumps("Invalid path")
        }

    lambda_function_name = context.function_name
    response = resource_fetcher.lambda_client.get_function_configuration(FunctionName=lambda_function_name)
    az = response['Environment']['Variables'].get('AWS_REGION')
    response = create_or_update_ecs_service(
                        consumer_name=consumer_name,
                        role=role, 
                        image=image,
                        az=az
                    )

    return response