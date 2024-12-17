from fastapi.testclient import TestClient
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import StaticPool
from faker import Faker

from fastapi_blend_db.app import (
    app,
    VirtualSession,
    get_virtual_session,
    Db1Base,
    Db2Base,
    User,
    Order,
)


@pytest.fixture
def session() -> Generator[VirtualSession, None, None]:
    """
    Create a virtual session with in-memory SQLite databases.
    Blend databases in a single virtual session.
    """
    # Create in-memory SQLite databases for both blended sessions
    db1_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    db2_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    Db1SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db1_engine)
    Db2SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db2_engine)

    with VirtualSession() as session:
        # Override the default sessions with the in-memory SQLite sessions
        session.db1_session = scoped_session(Db1SessionLocal)
        session.db2_session = scoped_session(Db2SessionLocal)

        # Ensure the tables are created
        Db1Base.metadata.create_all(bind=db1_engine)
        Db2Base.metadata.create_all(bind=db2_engine)

        yield session


@pytest.fixture
def dummy_data(session: Session):
    """
    Add dummy data to the database.
    """
    faker = Faker()
    faker.seed_instance(42)

    for _ in range(10):
        session.add(User(name=faker.name(), email=faker.email()))
        session.add(
            Order(
                item=faker.random_element(["Phone", "TV", "Computer"]),
                quantity=faker.random_int(min=1, max=10),
            )
        )

    session.commit()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_virtual_session] = lambda: session

    with TestClient(app) as client:
        yield client


def test_users_fetch(client: TestClient, dummy_data):
    response = client.get("/users")

    assert response.status_code == 200

    assert len(response.json()) == 10
    assert response.json()[0]["name"] == "Allison Hill"
    assert response.json()[0]["email"] == "donaldgarcia@example.net"


def test_orders_fetch(client: TestClient, dummy_data):
    response = client.get("/orders")

    assert response.status_code == 200

    assert len(response.json()) == 10
    assert response.json()[0]["item"] == "Computer"
    assert response.json()[0]["quantity"] == 2
