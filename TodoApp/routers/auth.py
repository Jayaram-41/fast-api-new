from typing import Annotated
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Users
from passlib.context import CryptContext
from jose import jwt, JWTError


router= APIRouter(
    prefix= '/auth',
    tags=['auth']
)

SECRET_KEY='06dc462962e10e8ad8d3a7515f7e6f97d826c4983b5ff389df95c00178122cd9'
ALGORITHM='HS256'


bcrypt_context=CryptContext(schemes=['bcrypt'], deprecated='auto')
oAuth2_bearer = OAuth2PasswordBearer(tokenUrl = 'auth/token')


class CreateUserRequest(BaseModel):
    email: str
    username:str
    firstname:str
    lastname:str
    password: str
    
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency= Annotated[Session, Depends(get_db)]


@router.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,create_user_request: CreateUserRequest):
    create_user_model=Users(
        email=create_user_request.email,
        username=create_user_request.username,
        firstname=create_user_request.firstname,
        lastname=create_user_request.lastname,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return create_user_model


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
         raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED,
                                detail= 'could not validate credentials')

    token = create_access_token(user.username, user.id, user.role,   timedelta(minutes=20)) 
    return {"access_token": token, "token_type": "bearer"}

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        print("password not matched")
        return False
    print("password matched")
    return user
    
def create_access_token(username: str, user_id: int,role: str, expires_delta: timedelta):
    encode = {'sub':username, 'id':user_id, 'role':role}
    expires= datetime.utcnow()+ expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
     

async def get_current_user(token: Annotated[str, Depends(oAuth2_bearer)]):
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms= [ALGORITHM])
        username= payload.get('sub')
        userid= payload.get('id')
        userrole=payload.get('role')
        if username is None or userid is None:
            raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED,
                                detail= 'could not validate credentials')
        return {'username': username, 'id': userid, 'role': userrole}
    except JWTError:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= 'could not validate user')
        