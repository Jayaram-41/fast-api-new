from operator import gt
from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Annotated
import models
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import Base, SessionLocal
from .auth import get_current_user
from pydantic import BaseModel
from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

router = APIRouter(
    prefix='/admin',
    tags=['Admin']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency= Annotated[Session, Depends(get_db)]
user_dependency= Annotated[dict, Depends(get_current_user)]

@router.get("/todo", status_code=status.HTTP_200_OK)
async def get_all(user:user_dependency, db:db_dependency):
    if user is None or user.get('userrole')!='Admin':
        raise HTTPException(status_code=401, detail="unAuthorized")
    return db.query(models.Todos).all()


@router.delete("/todo/{todoid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency,  todoid:int =Path(gt=0)):
    if user is None or user.get('userrole')!='Admin':
        raise HTTPException(status_code=401, detail="Un Authorized")
    todo_model=db.query(models.Todos).filter(models.Todos.id==user.get(id)).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.query(models.Todos).filter(models.Todos.id==user.get(id)).delete()
    db.commit()

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db_user = db.query(models.Users).filter(
        models.Users.id == user.get('id')
    ).first()

    return db_user

@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    user: user_dependency,
    db: db_dependency,
    request: PasswordChangeRequest
):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db_user = db.query(models.Users).filter(
        models.Users.id == user.get('id')
    ).first()

    # check old password
    if not bcrypt_context.verify(request.old_password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect old password")

    # update new password
    db_user.hashed_password = bcrypt_context.hash(request.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


