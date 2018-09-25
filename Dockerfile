FROM ubuntu:latest
MAINTAINER Rajdeep Dua "dua_rajdeep@yahoo.com"

# Update OS
RUN apt-get update -y

# Install Python
RUN apt-get install -y python-pip python-dev build-essential

# ADD . /app
COPY . /app
# ENV HOME /app
WORKDIR /app
RUN pip install -r requirements.txt
# RUN pip install uwsgi

ENTRYPOINT ["python"]
CMD ["app.py"]
