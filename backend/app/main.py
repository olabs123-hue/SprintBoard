"""SprintBoard: independently rebuilt task management API."""
from __future__ import annotations
import hashlib, hmac, os, secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
import jwt
from fastapi import Depends, FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import ForeignKey, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./sprintboard.db")
JWT_SECRET=os.getenv("JWT_SECRET","")
ENV=os.getenv("APP_ENV","development")
if ENV=="production" and len(JWT_SECRET)<32: raise RuntimeError("Production JWT_SECRET must be 32+ random characters")
if not JWT_SECRET: JWT_SECRET="local-development-only-do-not-use-in-production"
engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {},pool_pre_ping=True)
SessionLocal=sessionmaker(engine,expire_on_commit=False)
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    email:Mapped[str]=mapped_column(String(320),unique=True,index=True)
    name:Mapped[str]=mapped_column(String(100))
    password_hash:Mapped[str]=mapped_column(String(200))
class Task(Base):
    __tablename__="tasks"
    id:Mapped[int]=mapped_column(primary_key=True)
    owner_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    title:Mapped[str]=mapped_column(String(160))
    description:Mapped[str]=mapped_column(String(1000),default="")
    status:Mapped[str]=mapped_column(String(20),default="todo",index=True)
    priority:Mapped[str]=mapped_column(String(20),default="medium")
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc))
    owner:Mapped[User]=relationship()
Base.metadata.create_all(engine)
app=FastAPI(title="SprintBoard API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in os.getenv("FRONTEND_ORIGINS","http://localhost:5173").split(",") if x.strip()],allow_methods=["GET","POST","PATCH","DELETE"],allow_headers=["Authorization","Content-Type"])

class RegisterBody(BaseModel):
    model_config=ConfigDict(extra="forbid")
    name:str=Field(min_length=1,max_length=100)
    email:str=Field(min_length=3,max_length=320)
    password:str=Field(min_length=10,max_length=128)
class LoginBody(BaseModel):
    email:str
    password:str
class TokenResponse(BaseModel):
    access_token:str
    token_type:str="bearer"
Status=Literal["todo","in_progress","done"]
Priority=Literal["low","medium","high"]
class TaskCreate(BaseModel):
    model_config=ConfigDict(extra="forbid")
    title:str=Field(min_length=1,max_length=160)
    description:str=Field(default="",max_length=1000)
    status:Status="todo"
    priority:Priority="medium"
class TaskPatch(BaseModel):
    model_config=ConfigDict(extra="forbid")
    title:str|None=Field(default=None,min_length=1,max_length=160)
    description:str|None=Field(default=None,max_length=1000)
    status:Status|None=None
    priority:Priority|None=None
class TaskOut(BaseModel):
    id:int
    title:str
    description:str
    status:Status
    priority:Priority
    model_config=ConfigDict(from_attributes=True)
def db_session():
    with SessionLocal() as session:yield session
DB=Annotated[Session,Depends(db_session)]
def hash_password(password:str):
    salt=secrets.token_bytes(16)
    derived=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,310_000)
    return "pbkdf2_sha256$310000$"+salt.hex()+"$"+derived.hex()
def verify_password(password:str,encoded:str):
    try:
        kind,iterations,salt,digest=encoded.split("$")
        if kind!="pbkdf2_sha256": return False
        actual=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),int(iterations))
        return hmac.compare_digest(actual,bytes.fromhex(digest))
    except (ValueError,TypeError):return False
def token_for(user:User):
    now=datetime.now(timezone.utc)
    return jwt.encode({"sub":str(user.id),"iat":now,"exp":now+timedelta(hours=2)},JWT_SECRET,algorithm="HS256")
def current_user(db:DB,authorization:Annotated[str|None,Header()]=None):
    if not authorization or not authorization.startswith("Bearer "):raise HTTPException(401,"Authentication required")
    try:
        decoded=jwt.decode(authorization[7:],JWT_SECRET,algorithms=["HS256"])
        uid=int(decoded["sub"])
    except (jwt.PyJWTError,ValueError,KeyError) as exc:raise HTTPException(401,"Invalid or expired token") from exc
    user=db.get(User,uid)
    if user is None:raise HTTPException(401,"User no longer exists")
    return user
AuthUser=Annotated[User,Depends(current_user)]

@app.get("/api/health")
def health():return {"status":"ok"}
@app.post("/api/auth/register",response_model=TokenResponse,status_code=201)
def register(body:RegisterBody,db:DB):
    email=body.email.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):raise HTTPException(422,"Invalid email")
    if db.scalar(select(User.id).where(User.email==email)):raise HTTPException(409,"Email already registered")
    user=User(email=email,name=body.name.strip(),password_hash=hash_password(body.password))
    db.add(user)
    try:db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409,"Email already registered")
    db.refresh(user)
    return TokenResponse(access_token=token_for(user))
@app.post("/api/auth/login",response_model=TokenResponse)
def login(body:LoginBody,db:DB):
    user=db.scalar(select(User).where(User.email==body.email.strip().lower()))
    if not user or not verify_password(body.password,user.password_hash):raise HTTPException(401,"Invalid email or password")
    return TokenResponse(access_token=token_for(user))
@app.get("/api/me")
def me(user:AuthUser):return {"id":user.id,"name":user.name,"email":user.email}
@app.get("/api/tasks",response_model=list[TaskOut])
def list_tasks(db:DB,user:AuthUser,status:Status|None=None,priority:Priority|None=None,search:str=Query(default="",max_length=160)):
    stmt=select(Task).where(Task.owner_id==user.id)
    if status:stmt=stmt.where(Task.status==status)
    if priority:stmt=stmt.where(Task.priority==priority)
    if search:stmt=stmt.where(Task.title.ilike("%"+search.replace("%","\\%").replace("_","\\_")+"%",escape="\\"))
    return db.scalars(stmt.order_by(Task.id.desc())).all()
@app.post("/api/tasks",response_model=TaskOut,status_code=201)
def create_task(body:TaskCreate,db:DB,user:AuthUser):
    task=Task(owner_id=user.id,**body.model_dump())
    db.add(task);db.commit();db.refresh(task)
    return task
@app.patch("/api/tasks/{task_id}",response_model=TaskOut)
def update_task(task_id:int,body:TaskPatch,db:DB,user:AuthUser):
    task=db.scalar(select(Task).where(Task.id==task_id,Task.owner_id==user.id))
    if task is None:raise HTTPException(404,"Task not found")
    for key,value in body.model_dump(exclude_unset=True).items():
        if value is not None:setattr(task,key,value)
    db.commit();db.refresh(task)
    return task
@app.delete("/api/tasks/{task_id}",status_code=204)
def delete_task(task_id:int,db:DB,user:AuthUser):
    task=db.scalar(select(Task).where(Task.id==task_id,Task.owner_id==user.id))
    if task is None:raise HTTPException(404,"Task not found")
    db.delete(task);db.commit()
@app.get("/api/metrics")
def metrics(db:DB,user:AuthUser):
    rows=dict(db.execute(select(Task.status,func.count()).where(Task.owner_id==user.id).group_by(Task.status)).all())
    total=sum(rows.values());done=rows.get("done",0)
    return {"total":total,"in_progress":rows.get("in_progress",0),"completed":done,"completion_pct":round(done*100/total,1) if total else 0.0}
