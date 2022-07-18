from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete

import database.Table as Table


class APIDatabase:
    """Simple object to manage and queries DB"""

    def __init__(self, db_url):
        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def get_engine(self):
        """Returning DB engine"""
        return self.engine

    def close(self):
        """Close DB connection"""
        self.session.close()

    def clear(self, table: Table):
        """Just clear all entries from a table"""
        self.session.execute(delete(table))
        self.session.commit()

    def insert(self, *args: Table):
        self.session.add_all(args)
        self.session.commit()

    def execute(self, statement):
        """Execute any statement you want"""
        return self.session.execute(statement)

    def commit(self):
        """Commit into DB"""
        self.session.commit()
