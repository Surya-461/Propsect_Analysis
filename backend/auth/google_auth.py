import os
import json
import urllib.request
import urllib.parse
import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.user import User
from schemas.user import GoogleAuthRequest
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

def authenticate_google_user(req: GoogleAuthRequest, db: Session) -> User:
    configured_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    verified_email = None
    name = req.name
    picture = req.picture
    google_id = req.google_id

    # 1. Verification via Google ID Token (Credential)
    if req.credential:
        try:
            tokeninfo_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(req.credential)}"
            req_obj = urllib.request.Request(tokeninfo_url, headers={"User-Agent": "ProspectAI-Auth/3.1"})
            with urllib.request.urlopen(req_obj, timeout=8) as resp:
                if resp.status == 200:
                    info = json.loads(resp.read().decode("utf-8"))
                    # Validate audience if client ID is configured
                    token_aud = info.get("aud")
                    if configured_client_id and token_aud and token_aud != configured_client_id:
                        logger.warning("Google ID token audience mismatch: %s != %s", token_aud, configured_client_id)
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Google ID token audience does not match configured client ID."
                        )
                    verified_email = info.get("email")
                    name = info.get("name") or name or "Google User"
                    picture = info.get("picture") or picture
                    google_id = info.get("sub") or google_id
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("Google ID Token Verification Error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired Google credential: {e}"
            )

    # 2. Verification via Google OAuth 2.0 Access Token
    elif req.access_token:
        try:
            userinfo_url = f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={urllib.parse.quote(req.access_token)}"
            req_obj = urllib.request.Request(userinfo_url, headers={"User-Agent": "ProspectAI-Auth/3.1"})
            with urllib.request.urlopen(req_obj, timeout=8) as resp:
                if resp.status == 200:
                    info = json.loads(resp.read().decode("utf-8"))
                    verified_email = info.get("email")
                    name = info.get("name") or name or "Google User"
                    picture = info.get("picture") or picture
                    google_id = info.get("sub") or google_id
        except Exception as e:
            logger.warning("Google Access Token Verification Error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired Google access token: {e}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid Google ID token (credential) or access token is required for Google authentication."
        )

    if not verified_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account did not provide a verified email address."
        )

    clean_email = str(verified_email).strip().lower()
    user = UserRepository.get_by_email(db, clean_email)

    if user:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact administrator."
            )
        update_data = {}
        if google_id:
            update_data["google_id"] = google_id
        if picture:
            update_data["avatar_url"] = picture
        if name and (not user.name or user.name == "Google User"):
            update_data["name"] = name
        update_data["auth_provider"] = "google"
        user = UserRepository.update(db, user, **update_data)
    else:
        user = UserRepository.create(
            db=db,
            name=(name or "Google User").strip(),
            email=clean_email,
            auth_provider="google",
            google_id=google_id,
            avatar_url=picture,
            role="user",
            is_active=True
        )

    return user
