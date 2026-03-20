"""
IAM role and policy management.
Covers creating roles with trust policies, attaching managed policies,
listing roles and deleting roles cleanly.
"""
import json
import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION


iam = boto3.client("iam", region_name=AWS_REGION)


def create_role(role_name, service="ec2.amazonaws.com"):
    """
    Create an IAM role with a trust policy for a given AWS service.
    The trust policy allows the specified service to assume this role.
    Returns the Role ARN.

    Common service values:
        ec2.amazonaws.com
        lambda.amazonaws.com
        ecs-tasks.amazonaws.com
    """
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": service},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Created by aws-infra-automation for {service}",
        )
        arn = response["Role"]["Arn"]
        print(f"[OK] Created role: {role_name}  ({arn})")
        return arn

    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            print(f"[INFO] Role already exists: {role_name}")
            return iam.get_role(RoleName=role_name)["Role"]["Arn"]
        print(f"[ERROR] {e}")
        raise


def attach_policy(role_name, policy_arn):
    """
    Attach an AWS managed policy to a role.
    Find policy ARNs in the IAM console or AWS docs.
    Example: arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
    """
    try:
        iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        print(f"[OK] Attached {policy_arn} to {role_name}")
    except ClientError as e:
        print(f"[ERROR] {e}")
        raise


def list_roles(prefix=""):
    """
    List IAM roles in the account.
    Pass a prefix string to filter by role name, e.g. prefix='infra-'.
    """
    response = iam.list_roles()
    roles = []
    for r in response["Roles"]:
        if r["RoleName"].startswith(prefix):
            roles.append({
                "name":    r["RoleName"],
                "arn":     r["Arn"],
                "created": str(r["CreateDate"]),
            })
    return roles


def delete_role(role_name):
    """
    Detach all managed policies from a role then delete it.
    IAM requires policies to be detached before a role can be deleted.
    """
    try:
        attached = iam.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]
        for policy in attached:
            iam.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])
            print(f"[OK] Detached {policy['PolicyArn']} from {role_name}")

        iam.delete_role(RoleName=role_name)
        print(f"[OK] Deleted role: {role_name}")

    except ClientError as e:
        print(f"[ERROR] {e}")
        raise


if __name__ == "__main__":
    ROLE = "infra-automation-demo-role"

    arn = create_role(ROLE, service="ec2.amazonaws.com")
    attach_policy(ROLE, "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess")

    print("\n--- Roles with prefix 'infra-' ---")
    for role in list_roles(prefix="infra-"):
        print(f"  {role['name']}  {role['arn']}")

    delete_role(ROLE)
