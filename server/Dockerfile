# start from existing base image
FROM python:3.12-slim

# set working directorying inside the container
WORKDIR /app

# copy files from machine into the container
COPY requirements.txt .

# run command during build to install requirements
RUN pip install -r requirements.txt

# copy rest of the code
COPY . .

# tell docker which port the app is using
EXPOSE 9000

# command to run whent he container starts
CMD ["python3", "pulse.py"]