"""
Converts tech_available.csv into plain-text documents, uploads them to S3,
and triggers a Bedrock Knowledge Base sync.

Fill in KNOWLEDGE_BASE_ID before running.
"""

import os
import boto3
import csv
import json
import time

REGION = 'us-east-1'
S3_BUCKET = 'klaudprojekt'
KB_PREFIX = ''
KNOWLEDGE_BASE_ID = 'KSTQ6EAGQZ'
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'tech_available.csv')

s3 = boto3.client('s3', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)


def csv_row_to_text(row):
    """Convert a CSV row into a readable passage for the knowledge base."""
    return (
        f"Product ID: {row['Product ID']}\n"
        f"Name: {row['Name']}\n"
        f"Category: {row['Category']}\n"
        f"Stock available: {row['Stock']}\n"
        f"Support policy: {row['Support Policy']}\n"
    )


def upload_documents():
    print(f"Reading {CSV_PATH}...")
    with open(CSV_PATH, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Upload one text file per product so Bedrock can retrieve individual items
    for row in rows:
        product_id = row['Product ID']
        content = csv_row_to_text(row)
        key = f"{KB_PREFIX}{product_id}.txt"

        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=content.encode('utf-8'),
            ContentType='text/plain'
        )
        print(f"  Uploaded s3://{S3_BUCKET}/{key}")

    # Also upload a combined catalogue document
    combined = "Company IT Asset Catalogue\n\n" + "\n---\n".join(
        csv_row_to_text(r) for r in rows
    )
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=f"{KB_PREFIX}full_catalogue.txt",
        Body=combined.encode('utf-8'),
        ContentType='text/plain'
    )
    print(f"  Uploaded combined catalogue")


def sync_knowledge_base():
    if KNOWLEDGE_BASE_ID == 'FILL_IN_KB_ID':
        print("\nSkipping KB sync — fill in KNOWLEDGE_BASE_ID first.")
        return

    print(f"\nStarting ingestion job for KB: {KNOWLEDGE_BASE_ID}...")
    response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        dataSourceId='K9XGUUAZ17'
    )
    job_id = response['ingestionJob']['ingestionJobId']
    print(f"Ingestion job started: {job_id}")

    # Poll until complete
    while True:
        status_response = bedrock_agent.get_ingestion_job(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            dataSourceId='K9XGUUAZ17',
            ingestionJobId=job_id
        )
        status = status_response['ingestionJob']['status']
        print(f"  Status: {status}")
        if status in ('COMPLETE', 'FAILED'):
            break
        time.sleep(5)

    if status == 'COMPLETE':
        print("Knowledge base sync complete.")
    else:
        print("Ingestion job failed — check Bedrock console for details.")


if __name__ == '__main__':
    upload_documents()
    sync_knowledge_base()
