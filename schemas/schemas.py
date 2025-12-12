from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str
    date: str # YYYY-MM-DD

class Expense(ExpenseCreate):
    id: int
    user_id: str

class IncomeCreate(BaseModel):
    amount: float
    source: str = "Monthly Income"
    date: str

class Income(IncomeCreate):
    id: int
    user_id: str

class BudgetCreate(BaseModel):
    category: str
    amount: float
    month: str  # YYYY-MM

class Budget(BudgetCreate):
    id: int
    user_id: str

class BudgetSummary(BaseModel):
    category: str
    budgeted: float
    spent: float
    remaining: float
    percentage: float

class SpendingSummary(BaseModel):
    daily: float
    weekly: float
    monthly: float
    by_category: Dict[str, float]

class Recommendation(BaseModel):
    type: str
    title: str
    description: str
    savings: str

class Advice(BaseModel):
    category: str
    title: str
    content: str
    icon: str

class FinancialHealth(BaseModel):
    score: int
    status: str
    net_worth: float
    savings_rate: float
    debt_ratio: float

class DashboardStats(BaseModel):
    expenses: int
    categories: int
    items: int
    ai_insight: str

class PricePrediction(BaseModel):
    item: str
    current_price: float
    predicted_price: float
    predicted_increase: float
    confidence: float

class PriceHistory(BaseModel):
    dates: List[str]
    prices: List[float]
