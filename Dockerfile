FROM debian:latest
MAINTAINER Wenjing Ma

# Update OS
RUN apt-get update -y

# Install Python other things
#RUN apt-get install -y python-pip python-dev build-essential
RUN apt-get update && apt-get install -y apache2 \
    libapache2-mod-wsgi \
    build-essential \
    python \
    python-dev\
    python-pip \
    vim \
 && apt-get clean \
 && apt-get autoremove \
 && rm -rf /var/lib/apt/lists/*

# ADD . /app
COPY ./requirements.txt /var/www/apache-flask/requirements.txt
# RUN pip install uwsgi
RUN pip install -r /var/www/apache-flask/requirements.txt

# Copy over the apache configuration file and enable the site
COPY ./apache-flask.conf /etc/apache2/sites-available/apache-flask.conf
RUN a2ensite apache-flask
RUN a2enmod headers

COPY  . /var/www/apache-flask/

RUN a2dissite 000-default.conf
RUN a2ensite apache-flask.conf

EXPOSE 80

# ENV HOME /app change to apache-flask
WORKDIR /var/www/apache-flask
RUN chmod 777 /var/www/apache-flask/usercase
RUN chmod 777 /var/www/apache-flask/log



CMD /usr/sbin/apache2ctl -D FOREGROUND

# ENTRYPOINT ["python"]
# CMD ["app.py"]
