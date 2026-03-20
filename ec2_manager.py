"""
EC2 instance lifecycle management.
Covers listing, launching, stopping, starting, terminating and tagging instances.
"""
import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION, DEFAULT_TAGS


ec2 = boto3.client("ec2", region_name=AWS_REGION)


def list_instances(state_filter=None):
    """
    Return a list of EC2 instances in your account.
    Pass state_filter='running' or 'stopped' to narrow results.
    """
    filters = []
    if state_filter:
        filters.append({"Name": "instance-state-name", "Values": [state_filter]})

    response = ec2.describe_instances(Filters=filters)
    instances = []

    for reservation in response["Reservations"]:
        for inst in reservation["Instances"]:
            # Pull the Name tag if it exists, otherwise fall back to 'unnamed'
            name = next(
                (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
                "unnamed"
            )
            instances.append({
                "id":        inst["InstanceId"],
                "name":      name,
                "type":      inst["InstanceType"],
                "state":     inst["State"]["Name"],
                "public_ip": inst.get("PublicIpAddress", "N/A"),
                "launched":  str(inst["LaunchTime"]),
            })

    return instances


def launch_instance(name, instance_type="t2.micro", ami_id=None):
    """
    Launch a new EC2 instance and tag it automatically.
    Returns the new instance ID.

    Defaults to t2.micro which is free-tier eligible.
    ami_id defaults to Amazon Linux 2023 in eu-west-1.
    If you are in a different region update the AMI ID to match.
    """
    ami = ami_id or "ami-0905a3c97561e0b69"

    tags = [{"Key": "Name", "Value": name}]
    for key, value in DEFAULT_TAGS.items():
        tags.append({"Key": key, "Value": value})

    try:
        response = ec2.run_instances(
            ImageId=ami,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[{"ResourceType": "instance", "Tags": tags}],
        )
        instance_id = response["Instances"][0]["InstanceId"]
        print(f"[OK] Launched {instance_id} ({name}, {instance_type})")
        return instance_id
    except ClientError as e:
        print(f"[ERROR] Could not launch instance: {e}")
        raise


def stop_instance(instance_id):
    """Stop a running instance. The instance can be started again later."""
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"[OK] Stopping {instance_id}")
    except ClientError as e:
        print(f"[ERROR] {e}")
        raise


def start_instance(instance_id):
    """Start a stopped instance."""
    try:
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"[OK] Starting {instance_id}")
    except ClientError as e:
        print(f"[ERROR] {e}")
        raise


def terminate_instance(instance_id):
    """Terminate an instance permanently. This cannot be undone."""
    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        print(f"[OK] Terminating {instance_id}")
    except ClientError as e:
        print(f"[ERROR] {e}")
        raise


def tag_instance(instance_id, tags):
    """
    Add or update tags on an existing instance.
    Pass a plain dict like {"Env": "staging", "Owner": "gideon"}.
    """
    tag_list = [{"Key": k, "Value": v} for k, v in tags.items()]
    try:
        ec2.create_tags(Resources=[instance_id], Tags=tag_list)
        print(f"[OK] Tagged {instance_id}: {tags}")
    except ClientError as e:
        print(f"[ERROR] {e}")
        raise


if __name__ == "__main__":
    print("\n--- All instances ---")
    instances = list_instances()
    if not instances:
        print("  No instances found.")
    for inst in instances:
        print(f"  {inst['id']}  {inst['name']}  {inst['state']}  {inst['public_ip']}")
