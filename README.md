# AWS Infrastructure Automation

A Python command-line tool for provisioning and managing AWS resources using boto3. Covers the full resource lifecycle across EC2, S3 and IAM including automated tagging and safe teardown.

## What it does

- Launches, stops, starts and terminates EC2 instances
- Creates S3 buckets, uploads and downloads files and handles full bucket deletion
- Creates IAM roles with trust policies and attaches managed policies
- Tags every resource at creation so they are easy to find and clean up
- Bulk teardown script removes all managed resources to avoid surprise charges

## Project structure

```
Aws-Infra-Automation/
├── main.py          # CLI entry point
├── ec2_manager.py   # EC2 instance lifecycle
├── s3_manager.py    # S3 bucket and object operations
├── iam_manager.py   # IAM role creation and cleanup
├── cleanup.py       # Bulk teardown for all tagged resources
├── config.py        # Region and tag config from environment
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

**1. Clone and install dependencies**
```bash
git clone https://github.com/your-username/Aws-Infra-Automation.git
cd Aws-Infra-Automation
pip install -r requirements.txt
```

**2. Configure AWS credentials**

The cleanest way is via the AWS CLI:
```bash
aws configure
# Enter your Access Key ID, Secret Access Key and region (eu-west-1 for Ireland)
```

Or add them to your `.env` file (see `.env.example`).

A free AWS account gives you t2.micro instances and 5 GB S3 storage which is enough to run everything here.

**3. Set up your environment**
```bash
cp .env.example .env
# Edit .env if you want a different region
```

## Usage

**EC2**
```bash
python main.py ec2 list
python main.py ec2 launch --name dev-server
python main.py ec2 stop --id i-0abc123def456
python main.py ec2 terminate --id i-0abc123def456
```

**S3**
```bash
python main.py s3 create --name my-test-bucket
python main.py s3 upload --name my-test-bucket --file ./data.csv
python main.py s3 list --name my-test-bucket
python main.py s3 delete --name my-test-bucket
```

**IAM**
```bash
python main.py iam list
python main.py iam create-role --name MyLambdaRole
python main.py iam delete-role --name MyLambdaRole
```

**Cleanup everything**
```bash
python main.py cleanup
```

This finds and removes all EC2 instances and S3 buckets tagged `ManagedBy=Aws-Infra-Automation`.

## Run modules directly

Each manager file can also be run on its own for quick testing:
```bash
python ec2_manager.py   # lists all instances
python s3_manager.py    # creates a test bucket, uploads a file then deletes it
python iam_manager.py   # creates a demo role then deletes it
```

## Stack

- Python 3.11+
- boto3 (AWS SDK for Python)
- python-dotenv

## Notes

- Default region is eu-west-1 (Ireland). Change `AWS_REGION` in `.env` if needed
- t2.micro is free-tier eligible so short test runs cost nothing
- Always run `python main.py cleanup` after testing
