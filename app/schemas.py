from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatRequest(BaseModel):
    user_id: int
    conversation_id: int
    user_input: str

class ChatResponse(BaseModel):
    answer: str

class ConversationCreate(BaseModel):
    user_id: int
    conversation_type: Optional[str] = "default"

class UserCreate(BaseModel):
    email: str
    password: str
    nickname: str = ""
    business_type: str = ""
    
class SocialLoginRequest(BaseModel):
    provider: str            
    social_id: str
    email: str = None
    nickname: str = ""
    business_type: str = ""