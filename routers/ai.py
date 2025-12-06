from fastapi import APIRouter, Header, HTTPException, Query
from database import supabase
from schemas.schemas import Recommendation, Advice, FinancialHealth, DashboardStats, PricePrediction, PriceHistory
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import random
import joblib
import pandas as pd
import numpy as np
import os

router = APIRouter(prefix="/ai", tags=["AI"])

# Load ML Models and Data
try:
    ml_path = os.path.join(os.path.dirname(__file__), '..', 'ml')
    price_model = joblib.load(os.path.join(ml_path, 'price_prediction_model.pkl'))
    le_commodity = joblib.load(os.path.join(ml_path, 'commodity_encoder.pkl'))
    le_market = joblib.load(os.path.join(ml_path, 'market_encoder.pkl'))
    le_category = joblib.load(os.path.join(ml_path, 'category_encoder.pkl'))
    
    # Load WFP Dataset for historical data
    df = pd.read_csv(os.path.join(ml_path, 'wfp_food_prices_mwi.csv'), low_memory=False)
    # Basic preprocessing
    df = df[df['date'] != '#date'].copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['date', 'price', 'commodity', 'market'])
    
    print("ML Models and Dataset loaded successfully")
except Exception as e:
    print(f"Warning: ML models or dataset not found or failed to load: {e}")
    price_model = None
    df = None

def get_user_id(authorization: str) -> Optional[str]:
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "")
        import json
        import base64
        parts = token.split('.')
        if len(parts) != 3: return None
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4: payload += '=' * padding
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        return decoded.get('sub')
    except:
        return None

@router.get("/markets", response_model=List[str])
def get_markets():
    """Get list of available markets (cities)"""
    if df is None:
        return ["Lilongwe", "Blantyre", "Mzuzu", "Zomba"]
    return sorted(df['market'].unique().tolist())

@router.get("/commodities", response_model=List[str])
def get_commodities():
    """Get list of available food commodities"""
    if df is None:
        return ["Maize", "Rice", "Sugar", "Beans", "Groundnuts"]
    return sorted(df['commodity'].unique().tolist())

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(authorization: str = Header(None)):
    """Get dashboard statistics for the user"""
    user_id = get_user_id(authorization)
    
    if not user_id:
        return DashboardStats(
            expenses=0, categories=0, items=0,
            ai_insight="Sign in to see personalized insights."
        )
    
    try:
        expenses_response = supabase.table("expenses").select("*", count="exact").eq("user_id", user_id).execute()
        total_expenses = expenses_response.count if expenses_response.count else 0
        
        categories_response = supabase.table("expenses").select("category").eq("user_id", user_id).execute()
        unique_categories = len(set([exp.get("category") for exp in categories_response.data])) if categories_response.data else 0
        
        items_response = supabase.table("expenses").select("title").eq("user_id", user_id).execute()
        unique_items = len(set([exp.get("title") for exp in items_response.data])) if items_response.data else 0
        
        current_month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        monthly_expenses = supabase.table("expenses").select("amount").eq("user_id", user_id).gte("date", current_month_start).execute()
        total_monthly = sum([exp.get("amount", 0) for exp in monthly_expenses.data]) if monthly_expenses.data else 0
        
        if total_monthly > 200000:
            ai_insight = f"You've spent MK {total_monthly:,.2f} this month. Consider reviewing your largest expenses."
        elif total_monthly > 100000:
            ai_insight = f"Your spending is at MK {total_monthly:,.2f} this month. You're on track."
        elif total_expenses == 0:
            ai_insight = "Start tracking your expenses to get personalized insights."
        else:
            ai_insight = f"Great job! You've kept spending low at MK {total_monthly:,.2f} this month."
        
        return DashboardStats(
            expenses=total_expenses,
            categories=unique_categories,
            items=unique_items,
            ai_insight=ai_insight
        )
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        return DashboardStats(expenses=0, categories=0, items=0, ai_insight="Unable to load insights.")

def predict_price_change(item: str, market: str = "Lilongwe") -> dict:
    """Predict price change for an item using the ML model"""
    if not price_model:
        return {"predicted_increase": 0, "confidence": 0, "current_price": 0, "predicted_price": 0}
        
    try:
        today = datetime.now()
        next_month = today + timedelta(days=30)
        
        # Encode features
        try:
            commodity_encoded = le_commodity.transform([item])[0]
        except:
            return {"predicted_increase": 0, "confidence": 0, "current_price": 0, "predicted_price": 0}
            
        try:
            market_encoded = le_market.transform([market])[0]
        except:
            # Fallback to most common market if specific one not found
            market_encoded = le_market.transform(["Lilongwe"])[0]
        
        # Use 'Retail' category as default
        try:
            category_encoded = le_category.transform(["Retail"])[0]
        except:
            category_encoded = 0
        
        # Predict current price
        X_current = pd.DataFrame({
            'year': [today.year],
            'month': [today.month],
            'day_of_year': [today.timetuple().tm_yday],
            'commodity_encoded': [commodity_encoded],
            'market_encoded': [market_encoded],
            'category_encoded': [category_encoded]
        })
        
        current_price = price_model.predict(X_current)[0]
        
        # Predict future price
        X_future = pd.DataFrame({
            'year': [next_month.year],
            'month': [next_month.month],
            'day_of_year': [next_month.timetuple().tm_yday],
            'commodity_encoded': [commodity_encoded],
            'market_encoded': [market_encoded],
            'category_encoded': [category_encoded]
        })
        
        predicted_price = price_model.predict(X_future)[0]
        
        increase_pct = ((predicted_price - current_price) / current_price) * 100
        
        return {
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "predicted_increase": round(increase_pct, 1),
            "confidence": 0.85
        }
        
    except Exception as e:
        print(f"Prediction error for {item}: {e}")
        return {"predicted_increase": 0, "confidence": 0, "current_price": 0, "predicted_price": 0}

@router.get("/predictions/{item}", response_model=PricePrediction)
def get_price_prediction(item: str, market: str = Query("Lilongwe")):
    """Get price prediction for a specific item in a specific market"""
    
    prediction = predict_price_change(item, market)
    
    if prediction["current_price"] == 0:
         # Fallback mock data
        mock_data = {
            "Rice": {"current": 2750.0, "pred": 2890.0, "inc": 5.1},
            "Maize": {"current": 310.0, "pred": 315.0, "inc": 1.6},
            "Sugar": {"current": 1850.0, "pred": 2020.0, "inc": 9.2}
        }
        data = mock_data.get(item, {"current": 0, "pred": 0, "inc": 0})
        
        return PricePrediction(
            item=item,
            current_price=data["current"],
            predicted_price=data["pred"],
            predicted_increase=data["inc"],
            confidence=0.8
        )
    
    return PricePrediction(
        item=item,
        current_price=prediction["current_price"],
        predicted_price=prediction["predicted_price"],
        predicted_increase=prediction["predicted_increase"],
        confidence=prediction["confidence"]
    )

@router.get("/recommendations", response_model=List[Recommendation])
def get_recommendations(authorization: str = Header(None)):
    """Get personalized financial recommendations"""
    user_id = get_user_id(authorization)
    recs = []
    
    if not user_id: return []
        
    try:
        current_month = datetime.now().strftime("%Y-%m")
        
        income_res = supabase.table("income").select("amount").eq("user_id", user_id).gte("date", f"{current_month}-01").execute()
        total_income = sum([i['amount'] for i in income_res.data]) if income_res.data else 0
        
        expenses_res = supabase.table("expenses").select("*").eq("user_id", user_id).gte("date", f"{current_month}-01").execute()
        expenses = expenses_res.data
        total_expenses = sum([e['amount'] for e in expenses])
        
        budgets_res = supabase.table("budgets").select("*").eq("user_id", user_id).eq("month", current_month).execute()
        budgets = budgets_res.data
        
        spending_by_category = {}
        for e in expenses:
            cat = e['category']
            spending_by_category[cat] = spending_by_category.get(cat, 0) + e['amount']
            
        for budget in budgets:
            category = budget['category']
            limit = budget['amount']
            spent = spending_by_category.get(category, 0)
            
            if spent > limit:
                recs.append(Recommendation(
                    type="alert",
                    title=f"Over Budget: {category}",
                    description=f"You've exceeded your {category} budget by MK {spent - limit:,.0f}.",
                    savings=f"Save MK {spent - limit:,.0f}"
                ))
            elif spent > limit * 0.8:
                 recs.append(Recommendation(
                    type="warning",
                    title=f"Approaching Limit: {category}",
                    description=f"You've used {(spent/limit)*100:.0f}% of your {category} budget.",
                    savings="Monitor spending"
                ))
                
        # Price Prediction Recommendations
        common_commodities = ["Maize", "Rice", "Sugar", "Beans"]
        for item in common_commodities:
            pred = predict_price_change(item)
            if pred["predicted_increase"] > 3.0:
                recs.append(Recommendation(
                    type="prediction",
                    title=f"Price Alert: {item}",
                    description=f"{item} prices predicted to rise by {pred['predicted_increase']}% next month.",
                    savings=f"Save ~{pred['predicted_increase']}%"
                ))
                
        if total_income > 0:
            savings_rate = (total_income - total_expenses) / total_income
            if savings_rate < 0.1:
                recs.append(Recommendation(
                    type="saving",
                    title="Boost Your Savings",
                    description="Your savings rate is below 10%. Try the 50/30/20 rule.",
                    savings="Target 20% savings"
                ))
            elif savings_rate > 0.3:
                 recs.append(Recommendation(
                    type="invest",
                    title="Investment Opportunity",
                    description="You have a healthy surplus! Consider investing.",
                    savings="Grow your wealth"
                ))

    except Exception as e:
        print(f"Error generating recommendations: {e}")
        recs.append(Recommendation(
            type="info", title="Complete Your Profile",
            description="Add income and set budgets to get personalized recommendations.", savings="-"
        ))
        
    return recs

@router.get("/advices", response_model=List[Advice])
def get_advices(authorization: str = Header(None)):
    return [
        Advice(category="Budgeting", title="The 50/30/20 Rule", content="Allocate 50% to needs, 30% to wants, 20% to savings.", icon="📊"),
        Advice(category="Savings", title="Emergency Fund", content="Build a fund covering 3-6 months of expenses.", icon="🏦"),
        Advice(category="Investment", title="Start Small", content="Consistency matters more than the initial amount.", icon="📈"),
        Advice(category="Debt", title="Pay High-Interest First", content="Prioritize high-interest debts to save money.", icon="💳"),
    ]

@router.get("/financial-health", response_model=FinancialHealth)
def get_financial_health(authorization: str = Header(None)):
    user_id = get_user_id(authorization)
    if not user_id:
        return FinancialHealth(score=0, status="Unknown", net_worth=0.0, savings_rate=0.0, debt_ratio=0.0)
    
    try:
        # Get total income (all time)
        income_res = supabase.table("income").select("amount").eq("user_id", user_id).execute()
        total_income = sum([i['amount'] for i in income_res.data]) if income_res.data else 0
        
        # Get total expenses (all time)
        expenses_res = supabase.table("expenses").select("amount").eq("user_id", user_id).execute()
        total_expenses = sum([e['amount'] for e in expenses_res.data]) if expenses_res.data else 0
        
        # Calculate metrics
        net_worth = total_income - total_expenses
        
        # Calculate savings rate based on current month for better accuracy
        current_month = datetime.now().strftime("%Y-%m")
        month_income_res = supabase.table("income").select("amount").eq("user_id", user_id).gte("date", f"{current_month}-01").execute()
        month_income = sum([i['amount'] for i in month_income_res.data]) if month_income_res.data else 0
        
        month_expenses_res = supabase.table("expenses").select("amount").eq("user_id", user_id).gte("date", f"{current_month}-01").execute()
        month_expenses = sum([e['amount'] for e in month_expenses_res.data]) if month_expenses_res.data else 0
        
        savings_rate = 0
        if month_income > 0:
            savings_rate = max(0, (month_income - month_expenses) / month_income) * 100
            
        # Mock debt ratio for now (can be added to DB later)
        debt_ratio = 0.0
        
        # Calculate Score (0-100)
        # Weights: Savings Rate (40%), Net Worth (30%), Debt (30%)
        
        # Savings Score: Target 20% savings = 100 pts
        savings_score = min(savings_rate * 5, 100)
        
        # Net Worth Score: Target MK 1,000,000 = 100 pts (Adjust as needed)
        net_worth_score = min(max(net_worth, 0) / 10000, 100)
        
        # Debt Score: 0% debt = 100 pts
        debt_score = 100
        
        final_score = int((savings_score * 0.4) + (net_worth_score * 0.3) + (debt_score * 0.3))
        
        if final_score >= 80: status = "Excellent"
        elif final_score >= 60: status = "Good"
        elif final_score >= 40: status = "Fair"
        else: status = "Needs Improvement"
        
        return FinancialHealth(
            score=final_score, 
            status=status, 
            net_worth=round(net_worth, 2), 
            savings_rate=round(savings_rate, 1), 
            debt_ratio=round(debt_ratio * 100, 1)
        )
    except Exception as e:
        print(f"Error calculating financial health: {e}")
        return FinancialHealth(score=0, status="Error", net_worth=0.0, savings_rate=0.0, debt_ratio=0.0)

@router.get("/financial-history")
def get_financial_history(authorization: str = Header(None)):
    """Get monthly income vs expenses for the last 6 months"""
    user_id = get_user_id(authorization)
    if not user_id: return {"categories": [], "income": [], "expenses": []}
    
    try:
        months = []
        income_data = []
        expense_data = []
        
        for i in range(5, -1, -1):
            date = datetime.now() - timedelta(days=30 * i)
            month_str = date.strftime("%Y-%m")
            month_label = date.strftime("%b")
            months.append(month_label)
            
            # Start and end of month
            start_date = f"{month_str}-01"
            # Simple next month calculation
            if date.month == 12:
                end_date = f"{date.year + 1}-01-01"
            else:
                end_date = f"{date.year}-{date.month + 1:02d}-01"
            
            # Get Income
            inc_res = supabase.table("income").select("amount").eq("user_id", user_id).gte("date", start_date).lt("date", end_date).execute()
            inc_total = sum([x['amount'] for x in inc_res.data]) if inc_res.data else 0
            income_data.append(inc_total)
            
            # Get Expenses
            exp_res = supabase.table("expenses").select("amount").eq("user_id", user_id).gte("date", start_date).lt("date", end_date).execute()
            exp_total = sum([x['amount'] for x in exp_res.data]) if exp_res.data else 0
            expense_data.append(exp_total)
            
        return {
            "categories": months,
            "income": income_data,
            "expenses": expense_data
        }
    except Exception as e:
        print(f"Error fetching history: {e}")
        return {"categories": [], "income": [], "expenses": []}

@router.get("/prices/historical/{item}", response_model=PriceHistory)
def get_historical_prices(item: str, market: str = Query("Lilongwe")):
    """Get real historical price data for charting"""
    
    if df is None:
        # Fallback to mock data
        dates = []
        prices = []
        base_price = 1000
        for i in range(6, 0, -1):
            date = (datetime.now() - timedelta(days=30 * i)).strftime("%Y-%m-%d")
            price = base_price * (1 + random.uniform(-0.05, 0.08) * (6 - i) / 6)
            dates.append(date)
            prices.append(round(price, 2))
        return PriceHistory(dates=dates, prices=prices)
    
    try:
        # Filter data for specific item and market
        # Use case-insensitive matching if needed, but dataset usually consistent
        item_data = df[
            (df['commodity'] == item) & 
            (df['market'] == market)
        ].sort_values('date')
        
        if item_data.empty:
            # Try finding item in any market if specific market fails
            item_data = df[df['commodity'] == item].groupby('date')['price'].mean().reset_index().sort_values('date')
            
        # Get last 12 months of data
        last_year = item_data.tail(12)
        
        dates = last_year['date'].dt.strftime("%Y-%m-%d").tolist()
        prices = last_year['price'].tolist()
        
        if not dates:
             raise HTTPException(status_code=404, detail=f"No data found for {item} in {market}")
             
        return PriceHistory(dates=dates, prices=prices)
        
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

