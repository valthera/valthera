#!/usr/bin/env python3
"""
Test script for video upload functionality.
This script demonstrates how to use the video upload API.
"""

import requests
import base64
import json

# Configuration - Update these values
API_BASE_URL = "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/v1"
API_KEY = "your-api-key-here"  # Replace with actual API key

def test_video_upload():
    """Test the video upload endpoint."""
    
    # Create a small test video (just some dummy data)
    test_video_data = b"This is a test video file content"
    encoded_video = base64.b64encode(test_video_data).decode('utf-8')
    
    # Prepare the request
    url = f"{API_BASE_URL}/data"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "video_data": encoded_video,
        "file_name": "test_video.mp4"
    }
    
    print(f"📡 Sending video upload request to {url}")
    print(f"📁 File name: {payload['file_name']}")
    print(f"📊 Video size: {len(test_video_data)} bytes")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"🔁 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Video upload successful!")
            print(f"🎥 Video ID: {result.get('video_id')}")
            print(f"📁 File Name: {result.get('file_name')}")
            print(f"🗂️  S3 Key: {result.get('s3_key')}")
            print(f"💬 Message: {result.get('message')}")
        else:
            print(f"❌ Video upload failed!")
            print(f"📄 Response Body: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")

if __name__ == "__main__":
    print("🎬 Video Upload Test")
    print("=" * 50)
    
    if API_KEY == "your-api-key-here":
        print("⚠️  Please update the API_KEY variable with your actual API key")
        print("   You can get an API key by calling the /account/api/key endpoint")
    else:
        test_video_upload() 