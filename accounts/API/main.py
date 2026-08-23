import requests as request
from fastapi import FastAPI, HTTPException, status #not included in FastApi
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import mysql.connector
import secrets #Mooooooooooooooooore security than random. why? because
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init()
    yield
app = FastAPI(lifespan=lifespan)
#Fastapi instance named app for uvicorn

load_dotenv()
#loads dotenv files

ntfy = os.getenv("NTFY")
ntfy_timeout = 3
#timeout in seconds for ntfy-server response
ntfy_topic_test = "/TEST"
ntfy_topic_alert = os.getenv("NTFYALERT")
ntfy_topic_server = os.getenv("NTFYSERVER")

token_server = os.getenv("TOKEN")
username_ntfy = os.getenv("USERNAME")
password_ntfy = os.getenv("PASSWORD")

p1 = {"Title": "API-ACCOUNTS", "Priority" : "min"}
p2 = {"Title": "API-ACCOUNTS", "Priority" : "low"}
p3 = {"Title": "API-ACCOUNTS", "Priority" : "default"}
p4 = {"Title": "API-ACCOUNTS", "Priority" : "high"}
p5 = {"Title": "API-ACCOUNTS", "Priority" : "max"}
#ntfy-priorities put in var for better accesebility

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

default_message = "got test message"
wrong_token_message = "WARNING: api-request with wrong token"
ntfy_error_message = "Error at sending message to ntfy"
test_message = "test succesfull"
database_connection_error = "Script couldn't establish connection to database! Please check!"
api_request = "requested API"
api_request_through = "API requested valid"
database_init_succesfull = "succesfully initialized database"
#different messages put in var for better accesebility

def init():
    database = connect_to_database()
    #gets connection to database(named "database")
    if not database:
        return
    cursor = database.cursor()
    #needed to "write" into the database
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(64) PRIMARY KEY,
    account TEXT NOT NULL,
    password TEXT NOT NULL,
    steam_id BIGINT)
    """)
    #BIGINT: for bigger numbers

    database.commit()
    cursor.close()
    database.close()

    try:
        request.post(ntfy + ntfy_topic_server, data=database_init_succesfull.encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p3, timeout=ntfy_timeout)
    except Exception as e:
        print(ntfy_error_message + "\n" + database_init_succesfull)
    return
    

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=3306 #default port
        )
        return connection
    except mysql.connector.Error as err:
        request.post(ntfy + ntfy_topic_alert, data=database_connection_error.encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p4, timeout=ntfy_timeout)
        return None

def generate_id():
    database = connect_to_database()
    if not database:
        return None
    cursor = database.cursor()
 
    while True:
        generated_id = secrets.token_hex(32)
        query = "SELECT 1 FROM accounts WHERE id = %s LIMIT 1"
        cursor.execute(query, (generated_id,))

        result = cursor.fetchone()
        if result is None:
            break

    cursor.close()
    database.close()

    return generated_id


class Data(BaseModel):
    token: str | None = None
    account: str | None = None
    password: str | None = None
    user_id: str | None = None
    steam_id: str | None = None
#directly processes FastApi requests, assigns to dictionary und converts into selected data(here: str)

@app.post("/register")
async def test(data: Data):
    token_request = data.token
    account = data.account
    password = data.password
    if not token_request or not account or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing input")

    if not token_request == token_server:
        try:
            request.post(ntfy + ntfy_topic_alert, data=wrong_token_message.encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p4, timeout=ntfy_timeout)
        except Exception as e:
            problem = ntfy_error_message + "\n" + wrong_token_message
            print (problem)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Verification")
        #raise stops function, no return needed

    try:
        request.post(ntfy + ntfy_topic_server, data=api_request_through.encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p1, timeout=ntfy_timeout)
    except Exception as e:
        problem = ntfy_error_message + "\n" + api_request_through
        print (problem)

    user_id = generate_id()
    if not user_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="couldn't establish connection to internal database")

    database = connect_to_database()
    if not database:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="couldn't establish connection to internal database")
    cursor = database.cursor()

    query = "INSERT INTO accounts (id, account, password) VALUES (%s, %s, %s)"
    cursor.execute(query, (user_id, account, password))
    database.commit()

    cursor.close()
    database.close()
    
    return {"info": "request succesfull", "id": user_id}