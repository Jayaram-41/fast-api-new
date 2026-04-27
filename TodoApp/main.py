from fastapi import FastAPI
import models
from database import engine
from routers import auth, todos, admin


app = FastAPI()

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)

models.Base.metadata.create_all(bind=engine)
 