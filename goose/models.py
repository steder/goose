"""defines the models and mappers used to work
with the databases migration table.  

"""
import datetime

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import (Column, DateTime, Integer,
                        #ForeignKey,
                        MetaData,
                        #Sequence,
                        String, Table)

OperationalError = sqlalchemy.exc.OperationalError

max = func.max

metadata = MetaData()

migration_table = Table("migration_info", metadata,
    Column("migration_id", Integer, primary_key=True),
    Column("version", Integer),
    Column("name", String),
    Column("migration_date", DateTime, default=func.now(), onupdate=func.now()),
)

class Migration(object):
    def __init__(self, version, name, migrationDate=None):
        self.version = version
        self.name = name
        if migrationDate is None:
            migrationDate = datetime.datetime.now()
        self.migrationDate = migrationDate

    def __repr__(self):
        return "<Migration('%s', '%s', '%s')>"%(
            self.version, self.name, self.migrationDate)
        

from sqlalchemy.orm import mapper


mapper(Migration, migration_table)


from sqlalchemy.orm import sessionmaker
# autocommit=False is the default but then we're implicitly
# starting transactions instead of controlling them in our app.
Session = sessionmaker(autocommit=True,
                       autoflush=False)


def init():
    metadata.create_all()


def connect(dsn):
    engine = create_engine(dsn, echo=True)
    metadata.bind = engine
    Session.configure(bind=engine)
    session = Session()
    return session #, metadata, engine

    
