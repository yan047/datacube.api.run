# Version: 1.4
# Name: datacube.api.run
# for Python 3.6

FROM yan047/agdc2:1.7

MAINTAINER "boyan.au@gmail.com"

# In case someone loses the Dockerfile
RUN rm -rf /etc/Dockerfile
COPY Dockerfile /etc/Dockerfile

# set environment variables
ENV WORK_BASE /var/agdc
ENV DATACUBE_API_DIR "$WORK_BASE"/web

# must run with user root
USER root

# install dependencies
RUN conda install Flask -y --quiet

# copy datacube-ws source code to the image
COPY src "$DATACUBE_API_DIR" 

# change to work directory
WORKDIR "$DATACUBE_API_DIR"



