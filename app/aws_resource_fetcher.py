import boto3

import boto3

class AWSResourceFetcher:
    def __init__(self):
        self.ec2_client = boto3.client('ec2')
        self.elbv2_client = boto3.client('elbv2')
        self.lambda_client = boto3.client('lambda')
        self.dynamodb_client = boto3.client('dynamodb')
        self.s3_client = boto3.client('s3')
        self.ecs_client = boto3.client('ecs')
        self.iam_client = boto3.client('iam')
        self.tags = {
            "Application": "GPI-App",
            "Environment": "Development",
            "Owner": "Mohith"
        }

    def filter_by_tags(self, tags, resource_tags):
        """Checks if resource tags match the predefined tags."""
        tag_dict = {tag['Key']: tag['Value'] for tag in resource_tags}
        return all(tag_dict.get(k) == v for k, v in self.tags.items())

    def get_tags_for_resource(self, resource_id, resource_type):
        """Retrieves tags for a specific resource based on resource type."""
        if resource_type == 'subnet':
            tag_response = self.ec2_client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [resource_id]}])
        elif resource_type == 'lambda':
            tag_response = self.lambda_client.list_tags(Resource=resource_id)
        elif resource_type == 's3':
            tag_response = self.s3_client.get_bucket_tagging(Bucket=resource_id)
        elif resource_type == 'dynamodb':
            tag_response = self.dynamodb_client.list_tags_of_resource(ResourceArn=resource_id)
        elif resource_type == 'ecs':
            tag_response = self.ecs_client.list_tags_for_resource(resourceArn=resource_id)
        elif resource_type == 'iam':
            tag_response = self.iam_client.list_role_tags(RoleName=resource_id)
        elif resource_type == 'elbv2':
            tag_response = self.elbv2_client.list_tags_for_resource(ResourceArn=resource_id)
            return tag_response.get('Tags', [])
        else:
            return []

        return tag_response.get('Tags', tag_response.get('TagList', []))

    def get_alb(self):
        response = self.elbv2_client.describe_load_balancers()
        for alb in response['LoadBalancers']:
            alb_arn = alb['LoadBalancerArn']
            tags = self.get_tags_for_resource(alb_arn, 'elbv2')
            if self.filter_by_tags(tags, self.tags):
                return alb['DNSName']
        return None

    def get_vpc(self):
        response = self.ec2_client.describe_vpcs()
        for vpc in response['Vpcs']:
            vpc_id = vpc['VpcId']
            tags = self.get_tags_for_resource(vpc_id, 'subnet')
            if self.filter_by_tags(tags, self.tags):
                return vpc_id
        return None

    def get_subnets(self):
        response = self.ec2_client.describe_subnets()
        subnets = []
        for subnet in response['Subnets']:
            subnet_id = subnet['SubnetId']
            tags = self.get_tags_for_resource(subnet_id, 'subnet')
            if self.filter_by_tags(tags, self.tags):
                subnets.append(subnet_id)
        return subnets

    def get_lambda_functions(self):
        response = self.lambda_client.list_functions()
        functions = []
        for function in response['Functions']:
            function_arn = function['FunctionArn']
            tags = self.get_tags_for_resource(function_arn, 'lambda')
            if self.filter_by_tags(tags, self.tags):
                functions.append(function['FunctionName'])
        return functions

    def get_dynamodb_table(self, table_name):
        response = self.dynamodb_client.describe_table(TableName=table_name)
        table_arn = response['Table']['TableArn']
        tags = self.get_tags_for_resource(table_arn, 'dynamodb')
        if self.filter_by_tags(tags, self.tags):
            return boto3.resource('dynamodb').Table(table_name)
        return None

    def get_s3_buckets(self):
        response = self.s3_client.list_buckets()
        buckets = []
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            tags = self.get_tags_for_resource(bucket_name, 's3')
            if self.filter_by_tags(tags, self.tags):
                buckets.append(bucket_name)
        return buckets

    def get_ecs_clusters(self):
        response = self.ecs_client.list_clusters()
        clusters = []
        for cluster_arn in response['clusterArns']:
            tags = self.get_tags_for_resource(cluster_arn, 'ecs')
            if self.filter_by_tags(tags, self.tags):
                clusters.append(cluster_arn.split('/')[-1])
        return clusters

    def get_target_groups(self):
        response = self.elbv2_client.describe_target_groups()
        target_groups = []
        for tg in response['TargetGroups']:
            tg_arn = tg['TargetGroupArn']
            tags = self.elbv2_client.list_tags_for_resource(ResourceArn=tg_arn)['Tags']
            if any(tag['Key'] == 'Name' and tag['Value'] in ["GPI-target-group-admin", "GPI-target-group-user"]
                   for tag in tags):
                target_groups.append({
                    'TargetGroupArn': tg_arn,
                    'TargetGroupName': tg['TargetGroupName']
                })
        return target_groups

    def get_iam_role(self):
        response = self.iam_client.list_roles()
        for role in response['Roles']:
            role_name = role['RoleName']
            tags = self.get_tags_for_resource(role_name, 'iam')
            if self.filter_by_tags(tags, self.tags):
                return role['Arn']
        return None



# resource_fetcher = AWSResourceFetcher()
# alb_dns = resource_fetcher.get_alb()
# vpc_id = resource_fetcher.get_vpc()
# subnets = resource_fetcher.get_subnets()
# lambda_functions = resource_fetcher.get_lambda_functions()
# dynamodb_tables = resource_fetcher.get_dynamodb_tables()
# s3_buckets = resource_fetcher.get_s3_buckets()
# ecs_clusters = resource_fetcher.get_ecs_clusters()
# target_groups = resource_fetcher.get_target_groups()