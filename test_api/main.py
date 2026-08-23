import requests as request
from fastapi import FastAPI, HTTPException, status #not included in FastApi
import os
from dotenv import load_dotenv
from pydantic import BaseModel

app = FastAPI()
#Fastapi instance named app for uvicorn
load_dotenv()
#loads dotenv files

ntfy = os.getenv("NTFY")
ntfy_timeout = 3
#timeout in seconds for ntfy-server response
ntfy_topic_test = "/TEST"
ntfy_topic_alert = os.getenv("NTFYALERT")

token_server = os.getenv("TOKEN")
username_ntfy = os.getenv("USERNAME")
password_ntfy = os.getenv("PASSWORD")

p1 = {"Title": "DATABASE", "Priority" : "min"}
p2 = {"Title": "DATABASE", "Priority" : "low"}
p3 = {"Title": "DATABASE", "Priority" : "default"}
p4 = {"Title": "DATABASE", "Priority" : "high"}
p5 = {"Title": "DATABASE", "Priority" : "max"}
#ntfy-priorities put in var for better accesebility

default_message = "got test message"
wrong_token_message = "WARNING: api-request with wrong token"
ntfy_error_message = "Error at sending message to ntfy"
test_message = "test succesfull"
#different messages put in var for better accesebility

class Data(BaseModel):
    token: str | None = "NOTOKEN"
    content: str | None = None
#directly processes FastApi requests, assigns to dictionary und converts into selected data(here: str)

@app.post("/test")
async def test(data: Data):
    content = data.content
    token_request = data.token
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no content given")

    if not token_request == token_server:
        try:
            request.post(ntfy + ntfy_topic_alert, data=wrong_token_message.encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p4, timeout=ntfy_timeout)
        except Exception as e:
            problem = ntfy_error_message + "\n" + wrong_token_message
            print (problem)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Verification")
        #raise stops function, no return needed

    try:
        request.post(ntfy + ntfy_topic_test, data=content.encode('utf-8'), auth=(username_ntfy, password_ntfy), headers=p1, timeout=ntfy_timeout)
    except Exception as e:
        problem = ntfy_error_message + "\n" + content
        print (problem)
    
    print(content)
    return {"info": "test succesfull", "data": content}