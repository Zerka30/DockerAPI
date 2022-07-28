import docker
import os
import bcrypt
import datetime
import jwt
from flask import Flask, jsonify, request
from sqlalchemy import select
from functools import wraps

import config
from database.Database import APIDatabase
from database.Table import AccessToken, User

# Create Instance of Flask Server
app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "changeme")

# We have two type of token : access_token and user_token
# access_token never expires and is used for application
# user_token is used for user and is expired after 1 hours
# We have to create a new token everytime we want to use it
# We have to check if the token is valid everytime we want to use it


# decorator to verify that user has access to ressource
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" undefined")[0].strip()

        if not token:
            return jsonify({"status": "error", "message": "Token is missing !"}), 401

        try:
            # Decode JWT Token
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")

            # Database connection
            db = APIDatabase(config.DB_URL)

            if data["type"] == "access_token":
                query = select(AccessToken).filter(
                    AccessToken.user_id == AccessToken.get_user_by_uuid(data["uuid"]).id
                )
                access_token = db.execute(query).first()[0]
                return f(access_token, *args, **kwargs)
            elif data["type"] == "user_token":
                query = select(User).filter(User.uuid == data["uuid"])
                user = db.execute(query).first()[0]
                return f(user, *args, **kwargs)
            else:
                return (
                    jsonify({"status": "error", "message": "Invalid token type !"}),
                    400,
                )
        except Exception:
            return jsonify({"status": "error", "message": "Token is invalid !"}), 400

    return decorated


# decorator to verify that user has permission to permform action
def permission_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" undefined")[0].strip()

        if not token:
            return jsonify({"status": "error", "message": "Token is missing !"}), 401

        try:
            # Decode JWT Token
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")

            # Database connection
            db = APIDatabase(config.DB_URL)

            if data["type"] == "access_token":
                return (
                    jsonify({"status": "error", "message": "Invalid token type !"}),
                    403,
                )

            elif data["type"] == "user_token":
                query = select(User).filter(User.uuid == data["uuid"])
                user = db.execute(query).first()[0]

                if not user.permission:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "You don't have permission to do this !",
                            }
                        ),
                        401,
                    )

            else:
                return (
                    jsonify({"status": "error", "message": "Token is invalid !"}),
                    400,
                )

        except Exception:
            return jsonify({"status": "error", "message": "Token is invalid !"}), 400

        return f(user, *args, **kwargs)

    return decorated


# Create a login route that return a JWT Token
@app.route("/auth", methods=["POST"])
def auth():
    try:
        data = request.json
        username = data["username"]
        password = data["password"]
    except Exception:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    db = APIDatabase(config.DB_URL)
    query = select(User.username, User.password, User.uuid).filter(
        User.username == username
    )
    res = db.execute(query).all()

    if res == []:
        return jsonify({"status": "error", "message": "User not found"}), 401

    if bcrypt.checkpw(password.encode("utf-8"), res[0][1].encode("utf-8")):

        payload = {
            "uuid": res[0][2],
            "description": "This is a user token",
            "type": "user_token",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=45),
        }
        # Create JWT Token
        token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

        # Return a JWT Token as string
        return jsonify({"status": "success", "token": token})
    else:
        return jsonify({"status": "error", "message": "Invalid password"}), 401


# Create a route to register new user
@app.route("/register", methods=["POST"])
@permission_required
def register(active_user):
    try:
        data = request.json
        username = data["username"]
        password = data["password"]
        permission = data["permission"]
        create_token = data["create_token"]
    except Exception:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    db = APIDatabase(config.DB_URL)
    db.insert(
        User(
            username=username,
            password=password,
            permission=permission,
            create_token=create_token,
        )
    )

    return jsonify({"status": "success", "message": "User created"})


#  Route to create access token for a user
@app.route("/token", methods=["POST"])
@token_required
def token(jwt_user):
    # Verify that jwt_user is type of User
    if not isinstance(jwt_user, User):
        return jsonify({"status": "error", "message": "Invalid token type !"}), 401

    # Verify that user has permission to create token
    if not jwt_user.create_token:
        return (
            jsonify(
                {"status": "error", "message": "You don't have permission to do this !"}
            ),
            403,
        )

    # Get description from request
    try:
        description = request.json["description"]
    except Exception:
        description = None

    # Create a new access token
    db = APIDatabase(config.DB_URL)
    try:
        access_token = AccessToken(jwt_user.id, description)
        db.insert(access_token)
    except Exception as e:
        raise e

    return jsonify(
        {"status": "success", "message": "Token created", "token": access_token.token}
    )


# Route to return every users
@app.route("/api/v1/users", methods=["GET"])
@permission_required
def get_users(user):
    db = APIDatabase(config.DB_URL)
    query = select(
        User.id, User.username, User.permission, User.uuid, User.create_token
    )
    users = db.execute(query).all()

    data = []

    for user in users:
        dict = {
            "id": user.id,
            "uuid": user.uuid,
            "username": user.username,
            "permission": {
                "create_token": user.create_token,
                "admin": user.permission,
            },
        }

        data.append(dict)

    return jsonify({"status": "ok", "result": data})


def containers_status_json(container):
    return {
        "id": container.id,
        "name": container.name,
        "state": container.status,
        "specs": {
            "ram": container.attrs["HostConfig"]["Memory"],
            "cpu": container.attrs["HostConfig"]["CpuShares"],
            "image": container.attrs["Config"]["Image"],
        },
    }


# Route that return every docker container name and state
@app.route("/api/v1/status", methods=["GET"])
@token_required
def get_status(active_user):
    # Verify if containers is in query has parameter
    request_containers = []
    if "containers" in request.args:
        request_containers = request.args["containers"].split(",")

    client = docker.from_env()
    containers = client.containers.list(all=True)
    container_list = []
    for container in containers:
        if not request_containers:
            container_list.append(containers_status_json(container))
        else:
            if container.name in request_containers:
                container_list.append(containers_status_json(container))
    return jsonify(container_list)


# Route to start a container
@app.route("/api/v1/start/<string:container_name>", methods=["GET"])
@token_required
def start_container(active_user, container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    container.start()
    return jsonify({"message": "Container started"})


# Route to stop a container
@app.route("/api/v1/stop/<string:container_name>", methods=["GET"])
@token_required
def stop_container(active_user, container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    container.stop()
    return jsonify({"message": "Container stopped"})


# Route to restart a container
@app.route("/api/v1/restart/<string:container_name>", methods=["GET"])
@token_required
def restart_container(active_user, container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    container.restart()
    return jsonify({"message": "Container restarted"})


# Route for monitoring a container
@app.route("/health", methods=["GET"])
def healthcheck():
    return jsonify(
        {
            "state": "running",
        }
    )


if __name__ == "__main__":
    # Create root user if it doesn't exist
    db = APIDatabase(config.DB_URL)
    query = select(User).filter(User.username == "root")
    try:
        res = db.execute(query).one()
    except:
        res = None

    if not res:
        password = os.environ.get("ROOT_PASSWORD", "root")
        db.insert(User(username="root", password=password, permission=True))

    app.run(host="0.0.0.0", port=80, debug=True)
