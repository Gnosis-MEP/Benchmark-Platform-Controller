from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import sqlalchemy_jsonfield

from benchmark_platform_controller.conf import DATABASE_URL

# create declarative_base instance
Base = declarative_base()


# we create the class Book and extend it from the Base Class.
class ExecutionModel(Base):
    __tablename__ = 'execution'

    STATUS_RUNNING = 'RUNNING'
    STATUS_FINISHED = 'FINISHED'
    STATUS_CLEANUP = 'CLEANUP'

    id = Column(String(250), primary_key=True)
    shutdown_id = Column(String(250), nullable=True)
    status = Column(String(250), default=STATUS_RUNNING)
    json_results = Column(
        sqlalchemy_jsonfield.JSONField(
            # MariaDB does not support JSON for now
            enforce_string=True,
            # MariaDB connector requires additional parameters for correct UTF-8
            enforce_unicode=False
        ),
        nullable=True
    )

    # author = Column(String(250), nullable=False)
    # genre = Column(String(250))


# creates a create_engine instance at the bottom of the file
engine = create_engine(DATABASE_URL)

Base.metadata.create_all(engine)
Base.metadata.bind = engine
