From bitnami/spark:3.5.0

WORKDIR /opt/application/

RUN pip install nltk

#build the image and give it a name and a tag bitnami/sparknltk:latest to use it in the docker-compose