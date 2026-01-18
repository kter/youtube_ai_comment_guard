"""OAuth authentication routes for Google/YouTube login."""

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from youtube_guard.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory session store (use Redis/Firestore in production)
_sessions: dict[str, dict] = {}

# OAuth scopes required for YouTube comment management
YOUTUBE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _get_redirect_uri(request: Request) -> str:
    """Construct OAuth redirect URI from request or settings."""
    if settings.oauth_redirect_uri:
        return settings.oauth_redirect_uri
    
    # Construct from request
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost:8000"))
    return f"{scheme}://{host}/api/auth/callback"


def _get_oauth_flow(redirect_uri: str, state: Optional[str] = None) -> Flow:
    """Create OAuth flow with client configuration."""
    client_config = {
        "web": {
            "client_id": settings.youtube_client_id,
            "client_secret": settings.youtube_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=YOUTUBE_SCOPES,
        state=state,
    )
    flow.redirect_uri = redirect_uri
    
    return flow


def _get_session_id(request: Request) -> Optional[str]:
    """Get session ID from cookie."""
    return request.cookies.get("session_id")


def _get_session(session_id: str) -> Optional[dict]:
    """Get session data from store."""
    session = _sessions.get(session_id)
    if session and session.get("expires_at", datetime.min) > datetime.utcnow():
        return session
    return None


def _create_session(user_data: dict, credentials_json: str) -> str:
    """Create new session and return session ID."""
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = {
        "user": user_data,
        "credentials": credentials_json,
        "expires_at": datetime.utcnow() + timedelta(days=7),
    }
    return session_id


def _delete_session(session_id: str):
    """Delete session from store."""
    _sessions.pop(session_id, None)


@router.get("/login")
async def login(request: Request):
    """Initiate OAuth login flow."""
    if not settings.youtube_client_id or not settings.youtube_client_secret:
        raise HTTPException(
            status_code=500,
            detail="OAuth not configured. Please set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET."
        )
    
    redirect_uri = _get_redirect_uri(request)
    flow = _get_oauth_flow(redirect_uri)
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    
    # Store state for verification
    request.session["oauth_state"] = state
    
    return RedirectResponse(url=authorization_url)


@router.get("/callback")
async def callback(request: Request, code: str, state: Optional[str] = None):
    """Handle OAuth callback."""
    try:
        redirect_uri = _get_redirect_uri(request)
        flow = _get_oauth_flow(redirect_uri, state=state)
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info
        user_info_service = build("oauth2", "v2", credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        # Store credentials as JSON for YouTube API
        credentials_json = json.dumps({
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
        })
        
        user_data = {
            "id": user_info.get("id"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
        }
        
        # Create session
        session_id = _create_session(user_data, credentials_json)
        
        # Save credentials to Firestore for background processing
        if hasattr(request.app.state, "firestore"):
            await request.app.state.firestore.save_user_credentials(
                user_data["id"], 
                credentials_json
            )
        
        # Redirect to frontend with session cookie
        frontend_url = settings.frontend_url or "http://localhost:5173"
        response = RedirectResponse(url=frontend_url)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,  # Required for SameSite=none
            samesite="none",  # Required for cross-origin cookies
            max_age=7 * 24 * 60 * 60,  # 7 days
        )
        
        logger.info(f"User logged in: {user_data.get('email')}")
        return response
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        frontend_url = settings.frontend_url or "http://localhost:5173"
        return RedirectResponse(url=f"{frontend_url}?error=auth_failed")


@router.get("/me")
async def get_current_user(request: Request):
    """Get current authenticated user."""
    session_id = _get_session_id(request)
    if not session_id:
        return {"user": None}
    
    session = _get_session(session_id)
    if not session:
        return {"user": None}
    
    return {"user": session.get("user")}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Log out the current user."""
    session_id = _get_session_id(request)
    if session_id:
        _delete_session(session_id)
    
    response.delete_cookie(key="session_id")
    return {"message": "Logged out successfully"}


def get_user_credentials(request: Request) -> Optional[str]:
    """Get stored credentials for the current user (for use by other services)."""
    session_id = _get_session_id(request)
    if not session_id:
        return None
    
    session = _get_session(session_id)
    if not session:
        return None
    
    return session.get("credentials")
