import boto3
import os
import json
import uuid
import base64
import hashlib
from datetime import datetime, timezone

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
sqs = boto3.client("sqs")
table = dynamodb.Table(os.environ["USER_TABLE_NAME"])
video_bucket = os.environ["VIDEO_BUCKET_NAME"]
video_processor_queue_url = os.environ.get("VIDEO_PROCESSOR_QUEUE_URL")


def lambda_handler(event, context):
    
    try:
        # Step 1: Get API key ID from request context 
        # (API Gateway validates the key)
        try:
            api_key_id = event["requestContext"]["identity"]["apiKeyId"]
        except KeyError:
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "API key required"})
            }

        # Step 2: Look up user profile from API key ID
        user_id = get_user_id_from_api_key_id(api_key_id)
        if not user_id:
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Invalid API key"})
            }

        # Step 3: Parse request body
        body = json.loads(event.get("body", "{}"))
        video_data = body.get("video_data")  # Base64 encoded video
        file_name = body.get("file_name", f"video_{uuid.uuid4()}.mp4")
        
        if not video_data:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Video data required"})
            }

        # Step 4: Decode video data
        try:
            video_bytes = base64.b64decode(video_data)
        except Exception:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid video data format"})
            }

        # Step 5: Calculate MD5 hash and create folder name
        video_md5 = hashlib.md5(video_bytes).hexdigest()
        folder_name = video_md5
        
        # Create S3 key with user ID and folder structure
        s3_key = f"{user_id}/videos/{folder_name}/{file_name}"
        
        # Upload to S3
        s3.put_object(
            Bucket=video_bucket,
            Key=s3_key,
            Body=video_bytes,
            ContentType="video/mp4"
        )

        # Step 6: Store video metadata in DynamoDB
        video_id = str(uuid.uuid4())
        table.put_item(Item={
            "PK": f"video:{video_id}",
            "SK": f"user:{user_id}",
            "fileName": file_name,
            "s3Key": s3_key,
            "folderName": folder_name,
            "videoMd5": video_md5,
            "createdAt": datetime.utcnow().isoformat(),
            "fileSize": len(video_bytes)
        })

        # Step 7: Send to video processor queue if configured
        if video_processor_queue_url:
            try:
                message_body = {
                    "video_id": video_id,
                    "user_id": user_id,
                    "s3_key": s3_key,
                    "folder_name": folder_name,
                    "file_name": file_name,
                    "video_md5": video_md5,
                    "file_size": len(video_bytes),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                sqs.send_message(
                    QueueUrl=video_processor_queue_url,
                    MessageBody=json.dumps(message_body)
                )
                
                print(f"Sent video {video_id} to processing queue")
                
            except Exception as e:
                print(f"Error sending to video processor queue: {str(e)}")
                # Don't fail the request if queue sending fails

        # Step 8: Return success response
        return {
            "statusCode": 200,
            "body": json.dumps({
                "video_id": video_id,
                "file_name": file_name,
                "folder_name": folder_name,
                "s3_key": s3_key,
                "file_size": len(video_bytes),
                "message": "Video uploaded successfully"
            })
        }

    except Exception as e:
        print(f"Error in video creation: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }


def get_user_id_from_api_key_id(api_key_id):
    """
    Look up user ID from API key ID in DynamoDB.
    """
    try:
        response = table.query(
            IndexName="api_key_id-index",
            KeyConditionExpression="api_key_id = :api_key_id",
            ExpressionAttributeValues={
                ":api_key_id": api_key_id
            }
        )
        
        items = response.get("Items", [])
        if items:
            return items[0].get("user_id")
        
        return None
        
    except Exception as e:
        print(f"Error looking up user from API key: {str(e)}")
        return None
