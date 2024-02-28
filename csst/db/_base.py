from sqlalchemy.orm import DeclarativeBase


# declare our own base class that all of the modules in orm can import
class Base(DeclarativeBase):
    pass
