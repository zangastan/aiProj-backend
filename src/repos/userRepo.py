from sqlalchemy.orm import Session
from ..models.users import User
from ..schemas.users_schemas import UserResponse, Login, NewUser, UpdateUser
from ..utils import security
from ..supabase_client import supabase


class UserRepository:

    # -----------------------------
    # CREATE
    # -----------------------------
    def create_user(self, db: Session, user: NewUser):
        # Hash password
        # hashed_password = security.get_password_hash(user.password)

        data = {
            "email": user.email,
            "fullName": user.fullName,
            "hashed_password": user.password,
            # "role": user.role,
        }

        response = supabase.table("users").insert(data).execute()
        return response.data[0] if response.data else None

    # -----------------------------
    # READ
    # -----------------------------
    def get_user_by_email(self, db: Session, email: str):
        response = supabase.table("users").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None

    def get_user_by_id(self, db: Session, user_id: str):
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None

    def get_all_users(self, db: Session):
        response = supabase.table("users").select("*").execute()
        return response.data

    # -----------------------------
    # UPDATE
    # -----------------------------
    def update_user(self, db: Session, user_id: str, user: UpdateUser):
        # Convert pydantic model to dict and remove None values
        update_data = {k: v for k, v in user.model_dump().items() if v is not None}

        # If password is included, hash it
        if "password" in update_data:
            update_data["password"] = security.get_password_hash(update_data["password"])

        response = (
            supabase.table("users")
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )

        return response.data[0] if response.data else None

    # -----------------------------
    # DELETE
    # -----------------------------
    def delete_user(self, db: Session, user_id: str):
        response = (
            supabase.table("users")
            .delete()
            .eq("id", user_id)
            .execute()
        )
        return response.data[0] if response.data else None

