import os,tempfile
from pathlib import Path
TEST_DB=Path(tempfile.gettempdir())/f"sprintboard-test-{os.getpid()}.sqlite"
os.environ["DATABASE_URL"]=f"sqlite:///{TEST_DB}"
os.environ["APP_ENV"]="test"
from fastapi.testclient import TestClient
from app.main import app,Base,engine
import pytest

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
@pytest.fixture
def client():return TestClient(app)
def signup(client,email="one@example.com"):
    r=client.post("/api/auth/register",json={"name":"Test User","email":email,"password":"a-secure-password"})
    assert r.status_code==201,r.text
    return {"Authorization":"Bearer "+r.json()["access_token"]}
def test_health(client):assert client.get("/api/health").json()=={"status":"ok"}
def test_register_login_and_me(client):
    h=signup(client)
    assert client.get("/api/me",headers=h).json()["name"]=="Test User"
    assert client.post("/api/auth/login",json={"email":"one@example.com","password":"a-secure-password"}).status_code==200
def test_duplicate_registration(client):
    signup(client)
    assert client.post("/api/auth/register",json={"name":"Other","email":"one@example.com","password":"another-secure-password"}).status_code==409
def test_wrong_login(client):
    signup(client)
    assert client.post("/api/auth/login",json={"email":"one@example.com","password":"wrong-password"}).status_code==401
def test_missing_and_invalid_token(client):
    assert client.get("/api/tasks").status_code==401
    assert client.get("/api/tasks",headers={"Authorization":"Bearer invalid"}).status_code==401
def test_create_and_list(client):
    h=signup(client);r=client.post("/api/tasks",headers=h,json={"title":"Write tests","priority":"high"})
    assert r.status_code==201
    assert client.get("/api/tasks",headers=h).json()[0]["title"]=="Write tests"
def test_update_status(client):
    h=signup(client);id=client.post("/api/tasks",headers=h,json={"title":"Task"}).json()["id"]
    assert client.patch(f"/api/tasks/{id}",headers=h,json={"status":"done"}).json()["status"]=="done"
def test_delete(client):
    h=signup(client);id=client.post("/api/tasks",headers=h,json={"title":"Task"}).json()["id"]
    assert client.delete(f"/api/tasks/{id}",headers=h).status_code==204
    assert client.get("/api/tasks",headers=h).json()==[]
def test_ownership(client):
    h1=signup(client);id=client.post("/api/tasks",headers=h1,json={"title":"Secret"}).json()["id"]
    h2=signup(client,"two@example.com")
    assert client.get("/api/tasks",headers=h2).json()==[]
    assert client.patch(f"/api/tasks/{id}",headers=h2,json={"title":"Stolen"}).status_code==404
    assert client.delete(f"/api/tasks/{id}",headers=h2).status_code==404
def test_status_filter(client):
    h=signup(client)
    for status in ["todo","done"]:client.post("/api/tasks",headers=h,json={"title":status,"status":status})
    assert len(client.get("/api/tasks?status=done",headers=h).json())==1
def test_priority_filter(client):
    h=signup(client)
    for priority in ["low","high"]:client.post("/api/tasks",headers=h,json={"title":priority,"priority":priority})
    assert len(client.get("/api/tasks?priority=high",headers=h).json())==1
def test_search(client):
    h=signup(client)
    for title in ["Weekly report","Fix navigation"]:client.post("/api/tasks",headers=h,json={"title":title})
    assert client.get("/api/tasks?search=weekly",headers=h).json()[0]["title"]=="Weekly report"
def test_kpis(client):
    h=signup(client)
    for status in ["todo","in_progress","done","done"]:client.post("/api/tasks",headers=h,json={"title":"Demo "+status,"status":status})
    assert client.get("/api/metrics",headers=h).json()=={"total":4,"in_progress":1,"completed":2,"completion_pct":50.0}
def test_invalid_priority(client):
    h=signup(client)
    assert client.post("/api/tasks",headers=h,json={"title":"Invalid","priority":"urgent"}).status_code==422
def test_empty_kpis(client):
    h=signup(client)
    assert client.get("/api/metrics",headers=h).json()["completion_pct"]==0.0
