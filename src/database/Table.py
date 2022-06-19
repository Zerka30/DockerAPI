import bcrypt
import uuid
import jwt
import os
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, select
from sqlalchemy.ext.declarative import declarative_base

import config

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    uuid = Column("uuid", String(255), unique=True)
    username = Column("username", String(255), unique=True, nullable=False)
    password = Column("password", String(255), nullable=False)
    permission = Column("permissions", Boolean, default=False)
    create_token = Column("create_token", Boolean, default=False)

    def __init__(self, username, password, permission=False, create_token=False):
        self.username = username
        self.permission = permission
        self.uuid = self.generate_uuid()
        self.create_token = create_token
        # Use bcrypt to hash the password before storing it
        # Alos use salt store in .env file
        self.password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    def to_dict(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
            "username": self.username,
            "permission": self.permission,
        }

    def generate_uuid(self):
        return str(uuid.uuid4())


class AccessToken(Base):
    __tablename__ = "access_tokens"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    user_id = Column("user_id", Integer, ForeignKey("users.id"))
    token = Column("token", String(255), unique=True)
    description = Column("description", String(255))

    def __init__(self, user_id, description=None):
        self.user_id = user_id
        self.description = description
        self.token = self.create_token()

    @staticmethod
    def get_user_by_uuid(uuid):
        from database.Database import APIDatabase

        db = APIDatabase(config.DB_URL)
        query = select(User).filter(User.uuid == uuid)
        user = db.execute(query).one()[0]
        return user

    def get_user_uuid(self):
        from database.Database import APIDatabase

        db = APIDatabase(config.DB_URL)
        query = select(User.uuid).filter(User.id == self.user_id)
        uuid = db.execute(query).one()[0]
        return uuid

    def create_token(self):

        # If description is not provided, generate random string
        if not self.description:
            self.description = "Random: " + self.generate_uuid()

        payload = {
            "uuid": self.get_user_uuid(),
            "description": self.description,
            "type": "access_token",
        }

        token = jwt.encode(
            payload,
            os.environ.get("SECRET_KEY", "c203c9b4f36f89bb2c84cff8daaa9180"),
            algorithm="HS256",
        )

        return token
