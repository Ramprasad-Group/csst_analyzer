from pathlib import Path
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from csst.db.orm.polymer import Polymer


dotenv_path = Path(__file__).parent.absolute() / ".." / ".env"
load_dotenv(str(dotenv_path))
db_server = "postgresql+psycopg://{}:{}@{}:{}/{}".format(
    os.environ.get("CSST_DB_USER"),
    os.environ.get("CSST_DB_PASSWORD"),
    os.environ.get("CSST_DB_HOST"),
    int(os.environ.get("CSST_DB_PORT")),
    os.environ.get("CSST_DB_NAME"),
)
print(db_server)
engine = create_engine(db_server)
Session = sessionmaker(engine)
with Session() as session:
    print(session.query(Polymer).first())
