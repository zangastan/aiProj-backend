from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="SmartPurchase System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the SmartPurchase API"}

from routers import auth, expenses, ai, income, budgets

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(ai.router)
app.include_router(income.router)
app.include_router(budgets.router)
