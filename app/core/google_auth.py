from google.auth.transport import requests
from google.oauth2 import id_token
from typing import Optional, Dict, Any
from .config import settings


class GoogleOAuth:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Google OAuth token and return user info"""
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), self.client_id
            )

            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # Return user info
            return {
                'id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture'),
                'email_verified': idinfo.get('email_verified', False)
            }
        except ValueError as e:
            print(f"Token verification failed: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error during token verification: {e}")
            return None


google_oauth = GoogleOAuth()
