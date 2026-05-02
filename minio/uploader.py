import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin"
)

bucket_name = "test-bucket"

file_content = "Hello from Python uploader!"
file_name = "uploaded_file.txt"

s3.put_object(Bucket=bucket_name, Key=file_name, Body=file_content)
print(f"File {file_name} uploaded to {bucket_name}")
