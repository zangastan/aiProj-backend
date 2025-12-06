from fastapi import APIRouter, HTTPException, Header
from schemas.schemas import IncomeCreate, Income
from database import supabase
from typing import List
from datetime import datetime
import json
import base64
import os
from supabase import create_client

router = APIRouter(prefix="/income", tags=["Income"])

def get_authenticated_client(authorization: str):
    """Create a Supabase client with the user's JWT token for RLS"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    
    token = authorization.replace("Bearer ", "")
    
    # Decode JWT to get user ID
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        user_id = decoded.get('sub')
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user ID")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    # Create authenticated client with the JWT token
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    auth_client = create_client(url, key)
    auth_client.postgrest.auth(token)
    
    return user_id, auth_client

@router.get("/", response_model=List[Income])
def get_income(authorization: str = Header(None)):
    user_id, auth_client = get_authenticated_client(authorization)
    
    response = auth_client.table("income").select("*").eq("user_id", user_id).execute()
    return response.data

@router.get("/current")
def get_current_income(authorization: str = Header(None)):
    """Get current month's total income"""
    user_id, auth_client = get_authenticated_client(authorization)
    
    # Get current month in YYYY-MM format
    current_month = datetime.now().strftime("%Y-%m")
    
    response = auth_client.table("income").select("*").eq("user_id", user_id).gte("date", f"{current_month}-01").execute()
    
    total = sum(item["amount"] for item in response.data)
    
    return {"total": total, "records": response.data}

@router.post("/", response_model=Income)
def create_income(income: IncomeCreate, authorization: str = Header(None)):
    user_id, auth_client = get_authenticated_client(authorization)
    
    data = income.dict()
    data["user_id"] = user_id
    
    response = auth_client.table("income").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create income")
        
    return response.data[0]

@router.put("/{income_id}", response_model=Income)
def update_income(income_id: int, income: IncomeCreate, authorization: str = Header(None)):
    user_id, auth_client = get_authenticated_client(authorization)
    
    data = income.dict()
    
    response = auth_client.table("income").update(data).eq("id", income_id).eq("user_id", user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Income not found")
        
    return response.data[0]

@router.delete("/{income_id}")
def delete_income(income_id: int, authorization: str = Header(None)):
    user_id, auth_client = get_authenticated_client(authorization)
    
    response = auth_client.table("income").delete().eq("id", income_id).eq("user_id", user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Income not found")
        
    return {"message": "Income deleted successfully"}
