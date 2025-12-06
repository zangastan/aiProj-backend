from fastapi import APIRouter, HTTPException, Header
from schemas.schemas import UserRegister, UserLogin
from database import supabase

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(user: UserRegister):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    # 1. Sign up user in Supabase Auth
    try:
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "full_name": user.full_name
                }
            }
        })
        
        if not auth_response.user:
             raise HTTPException(status_code=400, detail="Registration failed")

        # 2. Insert into profiles table (if not handled by trigger)
        # For simplicity, we assume a trigger or manual insert might be needed if we store extra data
        # But Supabase Auth handles the user creation. We might want to store the profile in a public table.
        
        return {"message": "User registered successfully", "user": auth_response.user}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(user: UserLogin):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        # Try the newer method first, fall back to older method if it doesn't exist
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": user.email,
                "password": user.password
            })
            # Newer version has nested session
            session = auth_response.session
            user_data = auth_response.user
        except AttributeError:
            # Fallback for older supabase-py versions - use keyword arguments
            auth_response = supabase.auth.sign_in(
                email=user.email,
                password=user.password
            )
            # Older version: auth_response IS the session
            session = auth_response
            user_data = auth_response.user
        
        return {"access_token": session.access_token, "user": user_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile")
def get_profile(authorization: str = Header(None)):
    """Get current user profile"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        return user.user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/profile")
def update_profile(profile_data: dict, authorization: str = Header(None)):
    """Update user profile metadata"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    try:
        token = authorization.replace("Bearer ", "")
        
        # Update user metadata
        user = supabase.auth.update_user({
            "data": {
                "full_name": profile_data.get("full_name"),
                "phone": profile_data.get("phone"),
                "location": profile_data.get("location")
            }
        })
        
        return user.user
    except Exception as e:
        print(f"Error updating profile: {e}")
        raise HTTPException(status_code=400, detail=str(e))
