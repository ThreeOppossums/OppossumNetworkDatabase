import requests as request
from fastapi import FastAPI, HTTPException, status #not included in FastApi
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import mysql.connector
import secrets #Mooooooooooooooooore security than random. why? because
import bcrypt
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import logging
import time

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/api.log",
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"    
)

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
#MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

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
    database = None
    retries = 10

    while retries > 0:
        database = connect_to_database_accounts()
        #gets connection to database(named "database")

        if database:
            break

        time.sleep(2)
        retries -= 1
    
    if not database:
        try:
            request.post(ntfy + ntfy_topic_alert, data="code broke on init, no database".encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p5, timeout=ntfy_timeout)
        except Exception as e:
            logging.error(f"Can't post to NTFY: {e} Message: code broke on init: no database")
        return
    
    cursor = database.cursor()
    #needed to "write" into the database
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(64) PRIMARY KEY NOT NULL,
    account TEXT NOT NULL,
    password VARCHAR(255) NOT NULL,
    login_timeout INT NOT NULL,
    steam_id BIGINT)
    """)
    #BIGINT: for bigger numbers

    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS sessions (
    token VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
    )
    """)

    database.commit()
    cursor.close()
    database.close()

    try:
        request.post(ntfy + ntfy_topic_server, data=database_init_succesfull.encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p3, timeout=ntfy_timeout)
    except Exception as e:
        print(ntfy_error_message + "\n" + database_init_succesfull)
    return
    

def connect_to_database_accounts():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database="accounts",
            port=3306 #default port
        )
        return connection
    except mysql.connector.Error as err:
        try:
            request.post(ntfy + ntfy_topic_alert, data=f"{database_connection_error} ERROR: {err}".encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p4, timeout=ntfy_timeout)
        except Exception as e:
            logging.error(f"Can't post to NTFY: {e} MESSAGE: {database_connection_error} ERROR: {err}")
        return None

def generate_id():
    database = connect_to_database_accounts()
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

def generate_token():
    database = connect_to_database_accounts()
    if not database:
        return None
    cursor = database.cursor()
 
    while True:
        generated_token = secrets.token_hex(32)
        query = "SELECT 1 FROM sessions WHERE token = %s LIMIT 1"
        cursor.execute(query, (generated_token,))

        result = cursor.fetchone()
        if result is None:
            break

    cursor.close()
    database.close()

    return generated_token

def new_session(account_id: str):
    database = connect_to_database_accounts()
    if not database:
        return None
    cursor = database.cursor(dictionary=True)

    id = account_id

    query = "SELECT login_timeout FROM accounts WHERE id = %s LIMIT 1"
    cursor.execute(query, (id,))
    user = cursor.fetchone()
    if not user:
        return None

    token = generate_token()

    timeout = int(user["login_timeout"])

    created_at = datetime.now()
    expires_at = created_at + timedelta(minutes = timeout)

    query = "INSERT INTO sessions (account_id, token, created_at, expires_at) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (id, token, created_at, expires_at))
    database.commit()
    
    cursor.close()
    database.close()
    return token


class Data(BaseModel):
    token: str | None = None
    account: str | None = None
    password: str | None = None
    user_id: str | None = None
    steam_id: int | None = None
    session_key: str | None = None
    login_timeout: int | None = None
#directly processes FastApi requests, assigns to dictionary und converts into selected data(here: str)

@app.post("/register")
async def register(data: Data):
    token_request = data.token
    account = data.account
    password = data.password
    login_timeout_processing = 60
    logging.info('API --REGISTER-- called')
    if not token_request or not account or not password:
        missing = ""
        if not token_request:
            missing += "-TOKEN-"
        if not account:
            missing += "-ACCOUNT-"
        if not password:
            missing += "-PASSWORD-"

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing input: {missing}")

    if not token_request == token_server:
        try:
            request.post(ntfy + ntfy_topic_alert, data=wrong_token_message.encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p4, timeout=ntfy_timeout)
        except Exception as e:
            problem = ntfy_error_message + "\n" + wrong_token_message
            print (problem)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Verification")
        #raise stops function, no return needed

    database = connect_to_database_accounts()
    if not database:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="couldn't establish connection to internal database")
    cursor = database.cursor()
    
    query = "Select 1 FROM accounts WHERE account = %s LIMIT 1"
    cursor.execute(query, (account,))
    if cursor.fetchone():
        cursor.close()
        database.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account already exists")

    try:
        request.post(ntfy + ntfy_topic_server, data=api_request_through.encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p1, timeout=ntfy_timeout)
    except Exception as e:
        problem = ntfy_error_message + "\n" + api_request_through
        print (problem)

    password_hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    password_hashed = password_hashed_bytes.decode('utf-8')

    user_id = generate_id()
    if not user_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="couldn't establish connection to internal database")

    query = "INSERT INTO accounts (id, account, password, login_timeout) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (user_id, account, password_hashed, login_timeout_processing))
    database.commit()

    cursor.close()
    database.close()

    logging.info("API --REGISTER-- finished succesfully")
    
    return {"info": "request succesfull", "id": user_id}


@app.post("/login")
async def login(data: Data):
    token_request = data.token
    account = data.account
    password = data.password
    logging.info('API --LOGIN-- called')
    if not token_request or not account or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing input")
        
    if not token_request == token_server:
        try:
            request.post(ntfy + ntfy_topic_alert, data=wrong_token_message.encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p4, timeout=ntfy_timeout)
        except Exception as e:
            problem = ntfy_error_message + "\n" + wrong_token_message
            print(problem)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Verification")
        
    database = connect_to_database_accounts()
    cursor = database.cursor(dictionary=True)

    #load account from database
    query = "SELECT id, password FROM accounts WHERE account = %s LIMIT 1"
    cursor.execute(query, (account,))
    user = cursor.fetchone()

    cursor.close()
    database.close()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access")
        
    password_correct = bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8'))
        
    if not password_correct:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access")
    
    session_token = new_session(user["id"])

    logging.info("API --LOGIN-- finished succesfully")

    return {"info": "request succesfull", "token": session_token}

    #change connect_to_database to connect_to_database_accounts!!!