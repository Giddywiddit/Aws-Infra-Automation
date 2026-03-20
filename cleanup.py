"""
Cleanup script that removes all AWS resources tagged ManagedBy=aws-infra-automation.
Run this after testing to avoid unexpected charges.
"""
import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION


ec2 = boto3.client("ec2", region_name=AWS_REGION)
s3  = boto3.client("s3",  region_name=AWS_REGION)

MANAGED_BY_TAG = "aws-infra-automation"


def cleanup_tagged_instances():
    """Terminate all EC2 instances tagged ManagedBy=aws-infra-automation."""
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:ManagedBy",            "Values": [MANAGED_BY_TAG]},
            {"Name": "instance-state-name",       "Values": ["running", "stopped"]},
        ]
    )

    instance_ids = [
        inst["InstanceId"]
        for reservation in response["Reservations"]
        for inst in reservation["Instances"]
    ]

    if instance_ids:
        ec2.terminate_instances(InstanceIds=instance_ids)
        print(f"[OK] Terminated instances: {instance_ids}")
    else:
        print("[INFO] No tagged instances to clean up.")


def cleanup_tagged_buckets():
    """Delete S3 buckets tagged ManagedBy=aws-infra-automation."""
    all_buckets = s3.list_buckets().get("Buckets", [])

    for bucket in all_buckets:
        name = bucket["Name"]
        try:
            tags = s3.get_bucket_tagging(Bucket=name)["TagSet"]
            is_managed = any(
                t["Key"] == "ManagedBy" and t["Value"] == MANAGED_BY_TAG
                for t in tags
            )

            if not is_managed:
                continue

            # Empty the bucket before deleting (S3 requirement)
            objects = s3.list_objects_v2(Bucket=name).get("Contents", [])
            for obj in objects:
                s3.delete_object(Bucket=name, Key=obj["Key"])

            s3.delete_bucket(Bucket=name)
            print(f"[OK] Deleted bucket: {name}")

        except ClientError as e:
            # NoSuchTagSet means the bucket has no tags so we skip it
            if e.response["Error"]["Code"] == "NoSuchTagSet":
                continue
            print(f"[WARN] Skipped {name}: {e}")


if __name__ == "__main__":
    print("Running cleanup of tagged resources...")
    cleanup_tagged_instances()
    cleanup_tagged_buckets()
    print("Done.")
