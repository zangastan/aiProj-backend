from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.users_route import router as users_route
from .database import Base, engine

app = FastAPI(title="SmartPurchase")

Base.metadata.create_all(bind=engine)

# Allow requests from your frontend origin (Next.js dev server)
origins = [
    "http://localhost:3000", 
    "http://127.0.0.1:5500",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

app.include_router(users_route)

@app.get("/")
def main_app():
    return {"message": "Server running"}

#server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
