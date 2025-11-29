from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..schemas.users_schemas import Login, NewUser, UserResponse, UpdateUser, LoginResponse
from ..services.userServices import UserServices

router = APIRouter(prefix="/users", tags=["Users"])
service = UserServices()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# REGISTER NEW USER
# -----------------------------
@router.post("/register", response_model=UserResponse)
def register_user(user: NewUser, db: Session = Depends(get_db)):
    try:
        result = service.create_user(db, user)
        return result["user"]  # UserResponse expects user object
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# -----------------------------
# LOGIN USER
# -----------------------------
@router.post("/login", response_model=LoginResponse)
def login_user(user: Login, db: Session = Depends(get_db)):
    try:
        result = service.login(db, user)
        return {
            "success": True,
            "user": result["user"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# -----------------------------
# GET USER BY EMAIL
# -----------------------------
@router.get("/email/{email}", response_model=UserResponse)
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    try:
        result = service.get_user_by_email(db, email)
        return result["user"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------
# GET ALL USERS
# -----------------------------
@router.get("/", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    result = service.get_all_users(db)
    return result["users"]


# -----------------------------
# UPDATE USER
# -----------------------------
@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user: UpdateUser, db: Session = Depends(get_db)):
    try:
        result = service.update_user(db, user_id, user)
        return result["user"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------
# DELETE USER
# -----------------------------
@router.delete("/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    try:
        result = service.delete_user(db, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
