FROM python:3.11-slim 
#gets the python image

WORKDIR /app
#creats a temporary folder for the image

COPY requirements.txt .
#takes content of the requirements file and moves it to current dir (.)

RUN pip install --no-cache-dir -r requirements.txt
#installs packages in the workdir

COPY main.py .
#takes content of main.py and moves it to current dir (.)

EXPOSE 8000
#opens port 8000 for the api

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
#uvicorn: webserver for requests -- main:app: name of python file and name of api instance (app=FastAPI())
#--host and 0.0.0.0: makes that uvicorn listens to everything, not just localhost
#--port and 8000: sets the port for uvicorn