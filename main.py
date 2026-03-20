"""
AWS Infrastructure Automation
A command-line tool for provisioning and managing AWS resources using boto3.
Covers EC2 instances, S3 buckets and IAM roles.

Usage:
    python main.py ec2 list
    python main.py ec2 launch --name dev-server
    python main.py ec2 stop --id i-0abc123
    python main.py ec2 terminate --id i-0abc123

    python main.py s3 list
    python main.py s3 create --name my-bucket
    python main.py s3 upload --name my-bucket --file ./data.csv
    python main.py s3 delete --name my-bucket

    python main.py iam list
    python main.py iam create-role --name MyRole
    python main.py iam delete-role --name MyRole

    python main.py cleanup
"""
import argparse
import sys

import ec2_manager
import s3_manager
import iam_manager
from cleanup import cleanup_tagged_instances, cleanup_tagged_buckets


def handle_ec2(args):
    if args.subcommand == "list":
        instances = ec2_manager.list_instances()
        if not instances:
            print("No instances found.")
            return
        for inst in instances:
            print(f"  {inst['id']}  {inst['name']}  {inst['type']}  {inst['state']}  {inst['public_ip']}")

    elif args.subcommand == "launch":
        if not args.name:
            print("[ERROR] --name is required for launch")
            sys.exit(1)
        ec2_manager.launch_instance(name=args.name, instance_type=args.type)

    elif args.subcommand == "stop":
        if not args.id:
            print("[ERROR] --id is required for stop")
            sys.exit(1)
        ec2_manager.stop_instance(args.id)

    elif args.subcommand == "start":
        if not args.id:
            print("[ERROR] --id is required for start")
            sys.exit(1)
        ec2_manager.start_instance(args.id)

    elif args.subcommand == "terminate":
        if not args.id:
            print("[ERROR] --id is required for terminate")
            sys.exit(1)
        ec2_manager.terminate_instance(args.id)

    else:
        print(f"[ERROR] Unknown ec2 subcommand: {args.subcommand}")
        sys.exit(1)


def handle_s3(args):
    if args.subcommand == "list":
        objects = s3_manager.list_objects(args.name) if args.name else []
        if not args.name:
            print("[INFO] Pass --name <bucket> to list objects in a specific bucket.")
            return
        for obj in objects:
            print(f"  {obj['key']}  ({obj['size_kb']} KB)  {obj['modified']}")

    elif args.subcommand == "create":
        if not args.name:
            print("[ERROR] --name is required for create")
            sys.exit(1)
        s3_manager.create_bucket(args.name)

    elif args.subcommand == "upload":
        if not args.name or not args.file:
            print("[ERROR] --name (bucket) and --file (local path) are required for upload")
            sys.exit(1)
        s3_manager.upload_file(args.name, args.file)

    elif args.subcommand == "delete":
        if not args.name:
            print("[ERROR] --name is required for delete")
            sys.exit(1)
        s3_manager.delete_bucket(args.name)

    else:
        print(f"[ERROR] Unknown s3 subcommand: {args.subcommand}")
        sys.exit(1)


def handle_iam(args):
    if args.subcommand == "list":
        roles = iam_manager.list_roles()
        if not roles:
            print("No roles found.")
            return
        for role in roles:
            print(f"  {role['name']}  {role['arn']}")

    elif args.subcommand == "create-role":
        if not args.name:
            print("[ERROR] --name is required for create-role")
            sys.exit(1)
        iam_manager.create_role(args.name)

    elif args.subcommand == "delete-role":
        if not args.name:
            print("[ERROR] --name is required for delete-role")
            sys.exit(1)
        iam_manager.delete_role(args.name)

    else:
        print(f"[ERROR] Unknown iam subcommand: {args.subcommand}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="AWS Infrastructure Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("service", choices=["ec2", "s3", "iam", "cleanup"])
    parser.add_argument("subcommand", nargs="?", help="Action to run (list, create, launch, etc.)")
    parser.add_argument("--name", help="Resource name (bucket name or role name)")
    parser.add_argument("--id",   help="Instance ID for EC2 actions")
    parser.add_argument("--type", default="t2.micro", help="EC2 instance type (default: t2.micro)")
    parser.add_argument("--file", help="Local file path for S3 upload")

    args = parser.parse_args()

    try:
        if args.service == "ec2":
            handle_ec2(args)
        elif args.service == "s3":
            handle_s3(args)
        elif args.service == "iam":
            handle_iam(args)
        elif args.service == "cleanup":
            print("Running full cleanup of tagged resources...")
            cleanup_tagged_instances()
            cleanup_tagged_buckets()
            print("Done.")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
