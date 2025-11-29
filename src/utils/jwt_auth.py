from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "212ybvd629bdhdh829hhhbw6t2y2uwjhhhwbj9uw2y78t27tghsjbkhys782t6wt8u9uohjdfytd6wrd63$T&&@UGH@GG@DE@%&@f5%^T&*@Vc"
REFRESH_SECRET = "212ybvd629bdhdh829hhhbw6t2y2uwjhhhwbj9uw2y7ygey73ijndbvt3728iwknbvgrt3y28uikwjn"
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_minutes: int = 60):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_days: int = 7):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=expires_days)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET, algorithm=ALGORITHM)
