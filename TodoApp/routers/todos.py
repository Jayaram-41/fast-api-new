from operator import gt
from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Annotated
import models
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import Base, SessionLocal
from .auth import get_current_user


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency= Annotated[Session, Depends(get_db)]
user_dependency= Annotated[dict, Depends(get_current_user)]


class Todo(BaseModel):
    title: str= Field(min_length=3)
    description: str= Field(min_length=3, max_length=100)
    completed: bool = False
    priority: int = Field(ge=1, le=5)
    
    
@router.post("/todocreate/",status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency,todo:Todo, db:db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail= "authentication failed")
    
    todo_model=models.Todos(**todo.model_dump(), owner_id= user.get('id')) 
    db.add(todo_model)
    db.commit()
    return {"message": "Todo created successfully"}

@router.put("/todo/update/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user:user_dependency,id:int, todo:Todo, db:db_dependency):
    todo_model=db.query(models.Todos).filter(models.Todos.id==id)\
        .filter(models.Todos.owner_id==user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    else:
        todo_model.title=todo.title # type: ignore
        todo_model.description=todo.description # type: ignore
        todo_model.completed=todo.completed # type: ignore
        todo_model.priority=todo.priority # type: ignore
        db.add(todo_model)
        db.commit()
        return {"message": "Todo updated successfully"}
    


@router.get("/", status_code=status.HTTP_200_OK)
async def get_todos(user: user_dependency,db: db_dependency): 
    if user is None:
        raise HTTPException(status_code=401, detail='unauthorized')
    return db.query(models.Todos).filter(models.Todos.owner_id==user.get('id')).all()
    #return todos


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def get_todo(user:user_dependency,todo_id:int = Path(gt=0),db:db_dependency=None):
    if user is None:
        raise HTTPException(status_code=401, detail='un authorised')
    todo_model=db.query(models.Todos).filter(models.Todos.id==todo_id)\
        .filter(models.Todos.owner_id==user.get('id')).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail="Todo not found")


@router.delete("/todo/delete/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency,db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id)\
        .filter(models.Todos.owner_id==user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo_model)
    db.commit()