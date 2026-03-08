import boto3, os, time
from dotenv import load_dotenv
load_dotenv()

ec2 = boto3.client(
    'ec2',
    region_name=os.getenv('AWS_REGION', 'ap-south-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

INSTANCE_ID = 'i-0dfd37216dab239b1'
NEW_TYPE = 't2.small'

# Step 1: Stop instance
print(f"Stopping instance {INSTANCE_ID}...")
ec2.stop_instances(InstanceIds=[INSTANCE_ID])

print("Waiting for instance to stop...")
waiter = ec2.get_waiter('instance_stopped')
waiter.wait(InstanceIds=[INSTANCE_ID])
print("Instance stopped.")

# Step 2: Change type
print(f"Changing instance type to {NEW_TYPE}...")
ec2.modify_instance_attribute(
    InstanceId=INSTANCE_ID,
    InstanceType={'Value': NEW_TYPE}
)
print("Instance type changed.")

# Step 3: Start instance
print("Starting instance...")
ec2.start_instances(InstanceIds=[INSTANCE_ID])

print("Waiting for instance to be running...")
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=[INSTANCE_ID])

# Step 4: Get new IP
time.sleep(5)
r = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
i = r['Reservations'][0]['Instances'][0]
new_ip = i.get('PublicIpAddress', 'N/A')
print(f"Instance is running!")
print(f"Type: {i['InstanceType']}")
print(f"New Public IP: {new_ip}")
