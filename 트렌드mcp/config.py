# config.py
import os
from dotenv import load_dotenv
import json
import base64

load_dotenv()  # .env 파일을 읽어서 환경변수로 등록

SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NAVER_CLIENT_ID =os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET =os.getenv("NAVER_CLIENT_SECRET")


app_store_url = (
    "https://server.smithery.ai/@JiantaoFu/appinsightmcp/mcp"
    f"?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)
amazon_url = (
    f"https://server.smithery.ai/@SiliconValleyInsight/amazon-product-search/mcp"
    f"?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)

bright_data_url = (
    f"https://server.smithery.ai/@luminati-io/brightdata-mcp/mcp"
    f"?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)

youtube_config = {
    "youtubeTranscriptLang": "ko",
    "youtubeApiKey": GOOGLE_API_KEY
}
youtube_config_b64 = base64.b64encode(json.dumps(youtube_config).encode()).decode()

youtube_url = f"https://server.smithery.ai/@icraft2170/youtube-data-mcp-server/mcp?config={youtube_config_b64}&api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"

naver_config = {
    "NAVER_CLIENT_ID": NAVER_CLIENT_ID,
    "NAVER_CLIENT_SECRET": NAVER_CLIENT_SECRET
}
naver_config_b64 = base64.b64encode(json.dumps(naver_config).encode()).decode()
naver_url = (
    f"https://server.smithery.ai/@isnow890/naver-search-mcp/mcp"
    f"?config={naver_config_b64}&api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)