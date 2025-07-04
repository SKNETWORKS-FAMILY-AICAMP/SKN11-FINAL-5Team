from cryptography.fernet import Fernet
import base64
import os

FERNET_KEY = os.environ.get("FERNET_KEY")
fernet = Fernet(FERNET_KEY)

def encrypt_token(token: str) -> str:
    if token is None:
        return None
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(token_enc: str) -> str:
    if token_enc is None:
        return None
    return fernet.decrypt(token_enc.encode()).decode()
