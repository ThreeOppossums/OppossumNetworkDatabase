FROM python:3.11-slim 
#gets the python image

WORKDIR /app
#creats a temporary folder for the image

COPY requirements.txt
#takes content of the requirements file

RUN pip install --no-cache-dir -r requirements.txt
#installs packages in the workdir

COPY main.py
#takes content of main.py

CMD ["python3", "main.py"]
#runs command to run python script