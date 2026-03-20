"""
S3 bucket and object management.
Covers creating buckets, uploading and downloading files,
listing objects and full bucket deletion.
"""
import os
import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION, DEFAULT_TAGS


s3 = boto3.client("s3", region_name=AWS_REGION)


def create_bucket(bucket_name):
    """
    Create an S3 bucket in the configured region and tag it.
    Note: us-east-1 does not accept a LocationConstraint, every other
    region requires one. This function handles both cases.
    """
    try:
        if AWS_REGION == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
            )

        tag_set = [{"Key": k, "Value": v} for k, v in DEFAULT_TAGS.items()]
        s3.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={"TagSet": tag_set},
        )

        print(f"[OK] Created bucket: {bucket_name}")
        return True

    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "BucketAlreadyOwnedByYou":
            print(f"[INFO] Bucket already exists: {bucket_name}")
            return True
        print(f"[ERROR] {e}")
        raise


def upload_file(bucket_name, local_path, s3_key=None):
    """
    Upload a local file to an S3 bucket.
    If s3_key is not provided the filename is used as the key.
    Returns the full S3 URI on success.
    """
    key = s3_key or os.path.basename(local_path)
    try:
        s3.upload_file(local_path, bucket_name, key)
        uri = f"s3://{bucket_name}/{key}"
        print(f"[OK] Uploaded {local_path} to {uri}")
        return uri
    except ClientError as e:
        print(f"[ERROR] Upload failed: {e}")
        raise


def download_file(bucket_name, s3_key, local_path):
    """Download a file from S3 to a local path."""
    try:
        s3.download_file(bucket_name, s3_key, local_path)
        print(f"[OK] Downloaded s3://{bucket_name}/{s3_key} to {local_path}")
    except ClientError as e:
        print(f"[ERROR] Download failed: {e}")
        raise


def list_objects(bucket_name, prefix=""):
    """
    List objects in a bucket.
    Pass a prefix to filter results, e.g. prefix='logs/' to see only the logs folder.
    """
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        objects = []
        for obj in response.get("Contents", []):
            objects.append({
                "key":      obj["Key"],
                "size_kb":  round(obj["Size"] / 1024, 2),
                "modified": str(obj["LastModified"]),
            })
        print(f"[OK] Found {len(objects)} object(s) in {bucket_name}")
        return objects
    except ClientError as e:
        print(f"[ERROR] {e}")
        raise


def delete_object(bucket_name, s3_key):
    """Delete a single object from a bucket."""
    try:
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        print(f"[OK] Deleted s3://{bucket_name}/{s3_key}")
    except ClientError as e:
        print(f"[ERROR] {e}")
        raise


def delete_bucket(bucket_name):
    """
    Empty a bucket and then delete it.
    S3 requires a bucket to be empty before it can be deleted.
    """
    try:
        objects = list_objects(bucket_name)
        for obj in objects:
            delete_object(bucket_name, obj["key"])

        s3.delete_bucket(Bucket=bucket_name)
        print(f"[OK] Deleted bucket: {bucket_name}")
    except ClientError as e:
        print(f"[ERROR] {e}")
        raise


if __name__ == "__main__":
    BUCKET = "gideon-infra-test-bucket"
    TEST_FILE = "/tmp/test_upload.txt"

    with open(TEST_FILE, "w") as f:
        f.write("aws infra automation test\n")

    create_bucket(BUCKET)
    upload_file(BUCKET, TEST_FILE, "test/hello.txt")

    print("\n--- Objects in bucket ---")
    for obj in list_objects(BUCKET):
        print(f"  {obj['key']}  ({obj['size_kb']} KB)")

    delete_bucket(BUCKET)
