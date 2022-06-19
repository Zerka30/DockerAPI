<h3 align="center">Docker API</h3>

<div align="center">

  [![Status](https://img.shields.io/badge/status-active-success.svg)]() 

</div>

## 📝 Table of Contents

- [About](#about)
- [Informations](#informations)
- [How to run ?](#run)
- [Authors](#authors)

## 🧐 About <a name = "about"></a>

This project is a simple API written in python allowing to get the status of docker containers and to do various classical actions on them such as start them, stop them, or restart them.  

I'm currently using this API with a discord bot to manage game servers.  

Eventually, this API will be updated to work in a kubernetes cluster while keeping this goal of interraction with containers. 

This API is also secured with [JWT tokens](https://jwt.io/)


## ℹ Informations <a name = "informations"></a>

We use [gitmoji](https://gitmoji.dev/) for our commit messages

### Technologies we use
- [Python](https://www.python.org/) - Programming Language
- [MariaDB](https://mariadb.org/documentation/) - To store every data
- [Docker](https://www.docker.com/) - To deploy this api
- [JWT](https://jwt.io/) - To secure api access

### Python Librairies
- [Flask](https://flask.palletsprojects.com/en/2.1.x/) - To create the web server
- [SQLAlchemy](https://www.sqlalchemy.org/) - To manage database using python
- [Alembic](https://alembic.sqlalchemy.org/en/latest/) - For database migrations
- [Docker](https://docker-py.readthedocs.io/en/stable/) - To create interface with docker api and python

## ▶️​ How to run ? <a name = "run"></a>

If you want to put this application into production. Run docker-compose : 
`docker-compose up -d`

## ✍️ Authors <a name = "authors"></a>
- [@Zerka30](https://github.com/Zerka30) - creator and developer