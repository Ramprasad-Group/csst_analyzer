from pathlib import Path
import os
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pinrex.db.models.polymer import Polymer


dotenv_path = Path(__file__).parent.absolute() / ".." / ".env"
load_dotenv(str(dotenv_path))
server = SSHTunnelForwarder(
    (os.environ.get("SSH_TUNNEL_HOST"), int(os.environ.get("SSH_TUNNEL_PORT"))),
    ssh_username=os.environ.get("SSH_USERNAME"),
    ssh_password=os.environ.get("SSH_PASSWORD"),
    remote_bind_address=(
        os.environ.get("CSST_DB_HOST"),
        int(os.environ.get("CSST_DB_PORT")),
    ),
)

server.start()
db_server = "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
    os.environ.get("CSST_DB_USER"),
    os.environ.get("CSST_DB_PASSWORD"),
    os.environ.get("CSST_DB_HOST"),
    server.local_bind_port,
    os.environ.get("CSST_DB_NAME"),
)
engine = create_engine(db_server)
Session = sessionmaker(engine)
with Session() as session:
    print(session.query(Polymer).first().smiles)

server.stop()
