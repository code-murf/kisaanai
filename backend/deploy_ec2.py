import boto3
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

def deploy():
    print("Initializing deployment...")
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'ap-south-1')

    ec2 = boto3.client(
        'ec2',
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    vpc_id = 'vpc-08c82831d59a37f20'
    group_name = 'launch-wizard-1'
    description = 'launch-wizard-1 created 2026-02-28T15:51:04.919Z'
    group_id = None

    print(f"Creating security group '{group_name}' in VPC '{vpc_id}'...")
    try:
        response = ec2.create_security_group(
            GroupName=group_name,
            Description=description,
            VpcId=vpc_id
        )
        group_id = response['GroupId']
        print(f"Created Security Group ID: {group_id}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidGroup.Duplicate':
            print("Security group already exists. Retrieving GroupId...")
            response = ec2.describe_security_groups(
                Filters=[
                    {'Name': 'group-name', 'Values': [group_name]},
                    {'Name': 'vpc-id', 'Values': [vpc_id]}
                ]
            )
            group_id = response['SecurityGroups'][0]['GroupId']
            print(f"Found existing Security Group ID: {group_id}")
        else:
            raise e

    print(f"Authorizing ingress rules for '{group_id}'...")
    try:
        ec2.authorize_security_group_ingress(
            GroupId=group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ]
        )
        print("Ingress rules added successfully.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print("Ingress rules already exist. Skipping.")
        else:
            raise e

    print("Launching EC2 instance...")
    try:
        instances = ec2.run_instances(
            ImageId='ami-019715e0d74f695be',
            InstanceType='t2.micro',
            KeyName='Kisaan',
            MaxCount=1,
            MinCount=1,
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sda1',
                    'Ebs': {
                        'DeleteOnTermination': True,
                        'Iops': 3000,
                        'SnapshotId': 'snap-05228cd1dc9502ec6',
                        'VolumeSize': 20,
                        'VolumeType': 'gp3',
                        'Throughput': 125
                    }
                }
            ],
            NetworkInterfaces=[
                {
                    'AssociatePublicIpAddress': True,
                    'DeviceIndex': 0,
                    'Groups': [group_id]
                }
            ],
            CreditSpecification={
                'CpuCredits': 'standard'
            },
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'KisaanAI'}
                    ]
                }
            ],
            MetadataOptions={
                'HttpEndpoint': 'enabled',
                'HttpPutResponseHopLimit': 2,
                'HttpTokens': 'required'
            },
            PrivateDnsNameOptions={
                'HostnameType': 'ip-name',
                'EnableResourceNameDnsARecord': True,
                'EnableResourceNameDnsAAAARecord': False
            }
        )
        instance_id = instances['Instances'][0]['InstanceId']
        print(f"Successfully launched instance: {instance_id}")
    except Exception as e:
        print(f"Failed to launch instance: {e}")
        raise e

if __name__ == '__main__':
    deploy()
