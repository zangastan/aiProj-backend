from fastapi import APIRouter, HTTPException, Header
from schemas.schemas import BudgetCreate, Budget, BudgetSummary
from database import supabase
from typing import List
from datetime import datetime
import json
import base64
import os
from supabase import create_client

router = APIRouter(prefix="/budgets", tags=["Budgets"])

def get_authenticated_client(authorization: str):
    """Create a Supabase client with the token for RLS"""
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

@router.get("/", response_model=List[Budget])
def get_budgets(month: str = None, authorization: str = Header(None)):
    """Get budgets for a specific month (defaults to current month)"""
    user_id, auth_client = get_authenticated_client(authorization)
    
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    response = auth_client.table("budgets").select("*").eq("user_id", user_id).eq("month", month).execute()
    return response.data

@router.post("/", response_model=Budget)
def create_or_update_budget(budget: BudgetCreate, authorization: str = Header(None)):
    """Create or update a budget for a category"""
    user_id, auth_client = get_authenticated_client(authorization)
    
    # Check if budget already exists
    existing = auth_client.table("budgets").select("*").eq("user_id", user_id).eq("category", budget.category).eq("month", budget.month).execute()
    
    data = budget.dict()
    data["user_id"] = user_id
    
    if existing.data:
        # Update existing budget
        response = auth_client.table("budgets").update({"amount": budget.amount}).eq("id", existing.data[0]["id"]).execute()
    else:
        # Create new budget
        response = auth_client.table("budgets").insert(data).execute()
    
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create/update budget")
        
    return response.data[0]

@router.get("/summary", response_model=List[BudgetSummary])
def get_budget_summary(month: str = None, authorization: str = Header(None)):
    """Get budget vs actual spending summary"""
    user_id, auth_client = get_authenticated_client(authorization)
    
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # Get budgets for the month
    budgets_response = auth_client.table("budgets").select("*").eq("user_id", user_id).eq("month", month).execute()
    budgets = budgets_response.data
    
    # Get expenses for the month
    expenses_response = auth_client.table("expenses").select("*").eq("user_id", user_id).gte("date", f"{month}-01").lte("date", f"{month}-31").execute()
    expenses = expenses_response.data
    
    # Calculate spending by category
    spending_by_category = {}
    for expense in expenses:
        category = expense["category"]
        spending_by_category[category] = spending_by_category.get(category, 0) + float(expense["amount"])
    
    # Build summary
    summary = []
    for budget in budgets:
        category = budget["category"]
        budgeted = float(budget["amount"])
        spent = spending_by_category.get(category, 0)
        remaining = budgeted - spent
        percentage = (spent / budgeted * 100) if budgeted > 0 else 0
        
        summary.append({
            "category": category,
            "budgeted": budgeted,
            "spent": spent,
            "remaining": remaining,
            "percentage": percentage
        })
    
    return summary

@router.delete("/{budget_id}")
def delete_budget(budget_id: int, authorization: str = Header(None)):
    user_id, auth_client = get_authenticated_client(authorization)
    
    response = auth_client.table("budgets").delete().eq("id", budget_id).eq("user_id", user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    return {"message": "Budget deleted successfully"}
