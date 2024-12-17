# FastAPI Demo Application to Demonstrate How To Blend Two Databases

This is a demo application to demonstrate how to blend two databases using FastAPI.
Here we will use two SQLite databases, which are accessed via SQLAlchemy, but this can be easily adapted to any other databases.

A `VirtualSession` class is created to blend two databases. 
It can be used as a replacement for the `Session` class from SQLAlchemy to access both databases.
By using this `VirtualSession` class, both databases can be accessed as if they were a single database.

All relevant implementation details can be found in [app.py](./fastapi_blend_db/app.py).
The file [app_demo.py](./fastapi_blend_db/app_demo.py) contains a demo application that pre-filles the databases with some data.

To run the application, execute the following command:

```bash
poetry install
poetry run fastapi dev fastapi_blend_db/app_demo.py
```

Then go to the API docs at http://localhost:8000/docs.

