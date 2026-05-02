import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin"
)

bucket_name = "test-bucket"

response = s3.list_objects_v2(Bucket=bucket_name)

print(f"Files in bucket {bucket_name}:")
if "Contents" in response:
    for obj in response["Contents"]:
        print(f"  - {obj["Key"]} ({obj["Size"]} bytes)")
else:
    print("empty")
