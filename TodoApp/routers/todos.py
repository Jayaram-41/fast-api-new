from operator import gt

from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Annotated
import models
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import Base, SessionLocal


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency= Annotated[Session, Depends(get_db)]


class Todo(BaseModel):
    title: str= Field(min_length=3)
    description: str= Field(min_length=3, max_length=100)
    completed: bool = False
    priority: int = Field(ge=1, le=5)
    
    
@router.post("/todocreate/",status_code=status.HTTP_201_CREATED)
async def create_todo(todo:Todo, db:db_dependency):
    todo_model=models.Todos(**todo.model_dump())
    db.add(todo_model)
    db.commit()
    return {"message": "Todo created successfully"}

@router.put("/todo/update/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(id:int, todo:Todo, db:db_dependency):
    todo_model=db.query(models.Todos).filter(models.Todos.id==id).first()
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
async def get_todos(db: db_dependency): 
    todos = db.query(models.Todos).all()
    return todos


@router.get("/todo/{id}", status_code=status.HTTP_200_OK)
async def get_todo(id:int, db:db_dependency, todo_id:int = Path(gt=0 )):
    todo_model=db.query(models.Todos).filter(models.Todos.id==id).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail="Todo not found")


@router.delete("/todo/delete/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo_model)
    db.commit()