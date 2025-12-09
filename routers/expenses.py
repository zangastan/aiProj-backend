from fastapi import APIRouter, HTTPException, Header
from schemas.schemas import ExpenseCreate, Expense, SpendingSummary
from database import supabase
from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import json
import base64
import os
from supabase import create_client

router = APIRouter(prefix="/expenses", tags=["Expenses"])

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
    
    # Create a new client instance with the user's access token
    auth_client = create_client(url, key)
    # Set the auth token in the client's headers
    auth_client.postgrest.auth(token)
    
    return user_id, auth_client

@router.get("/", response_model=List[Expense])
def get_expenses(authorization: str = Header(None)):
    user_id, auth_client = get_authenticated_client(authorization)
    
    response = auth_client.table("expenses").select("*").eq("user_id", user_id).order("date", desc=True).execute()
    return response.data

@router.post("/", response_model=Expense)
def create_expense(expense: ExpenseCreate, authorization: str = Header(None)):
    user_id, auth_client = get_authenticated_client(authorization)
    
    data = expense.dict()
    data["user_id"] = user_id
    
    response = auth_client.table("expenses").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create expense")
        
    return response.data[0]

@router.get("/summary", response_model=SpendingSummary)
def get_spending_summary(authorization: str = Header(None)):
    """Get daily, weekly, and monthly spending summaries"""
    user_id, auth_client = get_authenticated_client(authorization)
    
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_start = today.replace(day=1)
    
    # Get all expenses for the month
    response = auth_client.table("expenses").select("*").eq("user_id", user_id).gte("date", str(month_start)).execute()
    expenses = response.data
    
    daily_total = 0
    weekly_total = 0
    monthly_total = 0
    by_category = defaultdict(float)
    
    for expense in expenses:
        expense_date = datetime.strptime(expense["date"], "%Y-%m-%d").date()
        amount = float(expense["amount"])
        category = expense["category"]
        
        # Monthly total
        monthly_total += amount
        by_category[category] += amount
        
        # Weekly total
        if expense_date >= week_ago:
            weekly_total += amount
        
        # Daily total
        if expense_date == today:
            daily_total += amount
    
    return {
        "daily": daily_total,
        "weekly": weekly_total,
        "monthly": monthly_total,
        "by_category": dict(by_category)
    }

@router.get("/by-category")
def get_expenses_by_category(authorization: str = Header(None)):
    """Get expenses grouped by category for pie chart"""
    user_id, auth_client = get_authenticated_client(authorization)
    
    # Get current month expenses
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    response = auth_client.table("expenses").select("*").eq("user_id", user_id).gte("date", month_start).execute()
    expenses = response.data
    
    by_category = defaultdict(float)
    for expense in expenses:
        by_category[expense["category"]] += float(expense["amount"])
    
    return {"data": dict(by_category)}

@router.get("/analytics")
def get_expense_analytics(authorization: str = Header(None)):
    """Get comprehensive analytics data for charts"""
    user_id, auth_client = get_authenticated_client(authorization)
    
    # Get last 30 days of expenses
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    response = auth_client.table("expenses").select("*").eq("user_id", user_id).gte("date", thirty_days_ago).execute()
    expenses = response.data
    
    # Group by date for trend line
    by_date = defaultdict(float)
    by_category = defaultdict(float)
    
    for expense in expenses:
        date = expense["date"]
        amount = float(expense["amount"])
        category = expense["category"]
        
        by_date[date] += amount
        by_category[category] += amount
    
    # Sort dates
    sorted_dates = sorted(by_date.keys())
    
    return {
        "trend": {
            "dates": sorted_dates,
            "amounts": [by_date[date] for date in sorted_dates]
        },
        "by_category": dict(by_category),
        "total": sum(by_category.values())
    }
