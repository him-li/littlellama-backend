import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-long-enough"

import importlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

main_module = importlib.import_module("app.main")


@pytest.fixture
def testing_session(tmp_path):
    database_path = tmp_path / "littlellama-test.db"
    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    try:
        yield session_factory
    finally:
        engine.dispose()


@pytest.fixture
def client(testing_session):
    def override_db():
        with testing_session() as session:
            yield session

    original_session = main_module.SessionLocal
    app.dependency_overrides[get_db] = override_db
    main_module.SessionLocal = testing_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        main_module.SessionLocal = original_session


@pytest.fixture
def db(testing_session):
    with testing_session() as session:
        yield session
