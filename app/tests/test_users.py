import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models import User

# Use um banco de dados de teste SQLite em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Substitua a dependência get_db para usar o banco de dados de teste
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_user(setup_database):
    # Teste de criação de um novo usuário
    response = client.post(
        "/users/",
        json={"name": "Test User", "cpf": "12345678900", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test User"
    assert "id" in response.json()
    
    # Verifique se o usuário foi realmente adicionado ao banco de dados
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == "test@example.com").first()
        assert user is not None
        assert user.name == "Test User"


def test_login_for_access_token(setup_database):
    # Primeiro, crie um usuário para poder fazer login
    client.post(
        "/users/",
        json={"name": "Login User", "cpf": "11111111111", "email": "login@example.com", "password": "password123"}
    )
    
    # Tente fazer login com as credenciais corretas
    response = client.post(
        "/users/token",
        data={"username": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    
    # Tente fazer login com credenciais incorretas
    response = client.post(
        "/users/token",
        data={"username": "login@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "access_token" not in response.json()