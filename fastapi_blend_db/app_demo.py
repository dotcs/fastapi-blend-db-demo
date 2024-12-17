from fastapi import FastAPI
from contextlib import asynccontextmanager
from faker import Faker

from fastapi_blend_db.app import (
    Db1Base,
    Db2Base,
    db1_engine,
    db2_engine,
    VirtualSession,
    User,
    Order,
    configure_endpoints,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Db1Base.metadata.create_all(bind=db1_engine)
    Db2Base.metadata.create_all(bind=db2_engine)

    faker = Faker()

    # Fill the databases with dummy data
    with VirtualSession() as session:
        for _ in range(10):
            session.add(User(name=faker.name(), email=faker.email()))
            session.add(
                Order(
                    item=faker.random_element(["Phone", "TV", "Computer"]),
                    quantity=faker.random_int(min=1, max=10),
                )
            )

        session.commit()

    yield


app = FastAPI(lifespan=lifespan)
configure_endpoints(app)
