FROM python:3.7

RUN apt-get update && apt-get install -y libgl1-mesa-glx

WORKDIR /app

# Copy application code and other files to the container
COPY . /app

# install dependency
RUN pip install -r requirements.txt

# Set the environment variable FLASK_APP. 
ENV FLASK_APP=app.py

# expose port

EXPOSE 5000

# The default command that is executed when the container starts

CMD ["flask", "run", "-h", "0.0.0.0"]

# docker image build -f ./Dockerfile -t flask_yolov3 .