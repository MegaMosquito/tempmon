# Web UI for my indoor/outdoortemperature monitor


# I really shouldn't put this in git. :-)
MY_OPENWEATHERMAP_APP_ID = '4a9bd3166311f9bb805b9a1fedb6f230'


# ----------------------------------------------------------------------------

IMAGE_NAME := 'ibmosquito/tempmon:1.0.0'

all: build run

# Build the docker container
build:
	docker build -t $(IMAGE_NAME) -f ./Dockerfile .

# Push the docker container to DockerHub
push:
	docker push $(IMAGE_NAME)

# Remove the local container image
clean:
	-docker rm -f $(IMAGE_NAME) 2>/dev/null || :
	-docker rmi -f $(IMAGE_NAME) 2>/dev/null || :

# ----------------------------------------------------------------------------

dev:
	-docker rm -f tempmon 2>/dev/null || :
	docker run -it -p 0.0.0.0:8000:6543 \
            --name tempmon --privileged --restart unless-stopped \
            -e MY_OPENWEATHERMAP_APP_ID=$(MY_OPENWEATHERMAP_APP_ID) \
            $(IMAGE_NAME) /bin/sh

run:
	-docker rm -f tempmon 2>/dev/null || :
	docker run -d -p 0.0.0.0:80:6543 \
            --name tempmon --privileged --restart unless-stopped \
            -e MY_OPENWEATHERMAP_APP_ID=$(MY_OPENWEATHERMAP_APP_ID) \
            $(IMAGE_NAME)


