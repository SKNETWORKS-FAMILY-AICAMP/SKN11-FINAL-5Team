import requests
import json
import sys

# ⚙️ 사전 세팅

# First verify the Instagram Business Account ID
IG_USER_ID = "17841458311607423"            # IG 비즈니스 사용자 ID
ACCESS_TOKEN = "EAAQ8cmB3yvsBPJUFdkxRpyq8OzltQQzS7VXIqwX3ezqJvKsZCOZBDmFh81kX10Ofc4OkT8J4Tms9J4UNwKPDpR2uTiUMZAcshUCGU9ewBWbVwWZBQqr3QknhmI6EFLinVZCH4gBMQbGDHq1Rir3IfkAdeO4r3XrXSXRs6EOqUHbiIYeGZBVBDWa3oTWtOMs1MZCo3GE5dWvZAZC1QekgPJMA8utHHPNDvL6uXKudDBAZDZD"  # 페이지 액세스 토큰
IMAGE_URL = "https://images.unsplash.com/photo-1503023345310-bd7c1de61c7d"  # 공개 접근 가능한 이미지 URL
CAPTION = "안녕하세요! 📸 #첫게시물"

def verify_account():
    url_verify = f"https://graph.facebook.com/v17.0/{IG_USER_ID}"
    params_verify = {"access_token": ACCESS_TOKEN, "fields": "id,username"}
    resp_verify = requests.get(url_verify, params=params_verify)
    resp_verify.raise_for_status()
    
    account_info = resp_verify.json()
    print(f"✅ Connected to Instagram Business Account: {account_info.get('username', 'Unknown')}")

def create_media_container():
    url_media = f"https://graph.facebook.com/v17.0/{IG_USER_ID}/media"
    params_media = {
        "image_url": IMAGE_URL,
        "caption": CAPTION,
        "access_token": ACCESS_TOKEN
    }
    resp_media = requests.post(url_media, params=params_media)
    resp_media.raise_for_status()
    
    creation_id = resp_media.json().get("id")
    if not creation_id:
        raise ValueError("Failed to get creation_id")
    return creation_id

def publish_media(creation_id):
    url_publish = f"https://graph.facebook.com/v17.0/{IG_USER_ID}/media_publish"
    params_pub = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }
    resp_pub = requests.post(url_publish, params=params_pub)
    resp_pub.raise_for_status()
    
    post_id = resp_pub.json().get("id")
    print("🎉 게시 성공! Instagram Post ID:", post_id)

try:
    verify_account()
    creation_id = create_media_container()
    publish_media(creation_id)

except requests.exceptions.RequestException as e:
    error_msg = "Unknown error occurred"
    error_code = None
    
    if hasattr(e, 'response') and e.response is not None:
        try:
            error_data = e.response.json().get('error', {})
            error_msg = error_data.get('message', str(e))
            error_code = error_data.get('code')
            
            if error_code == 190:
                print("❌ Error: Invalid or expired access token. Please refresh your access token.")
            elif error_code == 100:
                print("❌ Error: Invalid Instagram Business Account ID or insufficient permissions.")
                print("Please verify:")
                print("1. The account is a Business/Creator account")
                print("2. The access token has instagram_basic and instagram_content_publish permissions")
            else:
                print(f"❌ Error: {error_msg}")
                print(f"Error Code: {error_code}")
        except ValueError:
            print(f"❌ Error: {str(e)}")
            print("Response:", e.response.status_code, e.response.text)
    else:
        print(f"❌ Error: {str(e)}")
    sys.exit(1)

except ValueError as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)
