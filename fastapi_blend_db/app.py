from typing import Generator, Annotated
from fastapi import FastAPI, Depends
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import  DeclarativeBase, Query, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
from pydantic import BaseModel, ConfigDict

db1_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
db2_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

Db1SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db1_engine)
Db2SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db2_engine)

# Base classes
class Db1Base(DeclarativeBase): ...
class Db2Base(DeclarativeBase): ...

class User(Db1Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, index=True, unique=True)

class UserModel(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class Order(Db2Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, index=True)
    quantity = Column(Integer, index=True)

class OrderModel(BaseModel):
    id: int
    item: str
    quantity: int

    model_config = ConfigDict(from_attributes=True)

class VirtualSession:
    def __init__(self):
        self.db1_session = scoped_session(Db1SessionLocal)
        self.db2_session = scoped_session(Db2SessionLocal)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def query(self, model: type[DeclarativeBase]) -> Query:
        # Automatically detect the correct session based on the model's base class
        if model.__base__ == Db1Base:
            return self.db1_session.query(model)
        elif model.__base__ == Db2Base:
            return self.db2_session.query(model)
        else:
            raise ValueError("Model not recognized")
    
    def add(self, model: DeclarativeBase):
        if model.__class__.__base__ == Db1Base:
            self.db1_session.add(model)
        elif model.__class__.__base__ == Db2Base:
            self.db2_session.add(model)
        else:
            raise ValueError("Model not recognized")
    
    def commit(self):
        self.db1_session.commit()
        self.db2_session.commit()
    
    def close(self):
        self.db1_session.close()
        self.db2_session.close()

def get_virtual_session() -> Generator[VirtualSession, None, None]:
    with VirtualSession() as session:
        yield session

# fill some data when starting the app
@asynccontextmanager
async def lifespan(app: FastAPI):
    Db1Base.metadata.create_all(bind=db1_engine, checkfirst=False)
    Db2Base.metadata.create_all(bind=db2_engine, checkfirst=False)

    with VirtualSession() as session:
        session.add(User(name="John Doe", email="john@example.com"))
        session.add(Order(item="Phone", quantity=2))

        session.commit()
    
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/users")
def read_users(session: Annotated[VirtualSession, Depends(get_virtual_session)]) -> list[UserModel]:
    users = session.query(User).all()
    return [UserModel.model_validate(user) for user in users]

@app.get("/orders")
def read_orders(session: Annotated[VirtualSession, Depends(get_virtual_session)]) -> list[OrderModel]:
    orders = session.query(Order).all()
    return [OrderModel.model_validate(order) for order in orders]
