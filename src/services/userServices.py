from sqlalchemy.orm import Session
from ..repos.userRepo import UserRepository
from ..schemas.users_schemas import Login, NewUser
from ..utils import security
from ..utils.jwt_auth import create_access_token, create_refresh_token


class UserServices:
    def __init__(self):
        self.repo = UserRepository()

    # -----------------------------
    # CREATE USER
    # -----------------------------
    def create_user(self, db: Session, data: NewUser):
        new_user = self.repo.create_user(db, data)
        if not new_user:
            raise Exception("Failed to create user")
        return {"success": True, "user": new_user}

    # -----------------------------
    # READ USER
    # -----------------------------
    def get_user_by_email(self, db: Session, email: str):
        user = self.repo.get_user_by_email(db, email)
        if not user:
            raise Exception("User not found")
        return {"success": True, "user": user}

    # -----------------------------
    # LOGIN
    # -----------------------------
    def login(self, db: Session, data: Login):
        # get user by email
        user_record = self.repo.get_user_by_email(db, data.email)
        if not user_record:
            raise Exception("E-mail or Password incorrect")

        # verify password
        if not security.verify_password(data.password, user_record.get("password")):
            raise Exception("E-mail or Password incorrect")

        # generate tokens
        access_token = create_access_token({"id": user_record["id"], "email": user_record["email"]})
        refresh_token = create_refresh_token({"id": user_record["id"]})

        return {
            "success": True,
            "user": user_record,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    # -----------------------------
    # ALL USERS
    # -----------------------------
    def get_all_users(self, db: Session):
        users = self.repo.get_all_users(db)
        return {"success": True, "users": users}

    # -----------------------------
    # UPDATE USER
    # -----------------------------
    def update_user(self, db: Session, user_id: str, data):
        updated_user = self.repo.update_user(db, user_id, data)
        if not updated_user:
            raise Exception("User not found")
        return {"success": True, "user": updated_user}

    # -----------------------------
    # DELETE USER
    # -----------------------------
    def delete_user(self, db: Session, user_id: str):
        deleted_user = self.repo.delete_user(db, user_id)
        if not deleted_user:
            raise Exception("User not found")
        return {"success": True, "message": "User deleted successfully"}
