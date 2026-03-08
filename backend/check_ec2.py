import boto3, os
from dotenv import load_dotenv
load_dotenv()

ec2 = boto3.client(
    'ec2',
    region_name=os.getenv('AWS_REGION', 'ap-south-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

r = ec2.describe_instances(InstanceIds=['i-0dfd37216dab239b1'])
i = r['Reservations'][0]['Instances'][0]
print(f"Type: {i['InstanceType']}")
print(f"State: {i['State']['Name']}")
print(f"IP: {i.get('PublicIpAddress', 'N/A')}")
