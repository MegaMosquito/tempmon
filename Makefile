# Web UI for my indoor/outdoortemperature monitor

# ----------------------------------------------------------------------------

IMAGE_NAME := 'ibmosquito/tempmon:1.0.0'

all: build run

# Build the docker container
build:
	docker build -t $(IMAGE_NAME) -f ./Dockerfile .

# Push the docker container to DockerHub
push:
	docker push $(IMAGE_NAME)

# Test local temperature REST API
test:
	curl -sS http://localhost:80/temp | jq .

# Remove the local container image
clean:
	-docker rm -f $(IMAGE_NAME) 2>/dev/null || :
	-docker rmi -f $(IMAGE_NAME) 2>/dev/null || :

# ----------------------------------------------------------------------------

dev:
	#xhost +
	-docker rm -f tempmon 2>/dev/null || :
	docker run -it \
            --name tempmon \
            --privileged \
            -p 0.0.0.0:80:80 \
            --name tempmon --privileged \
            --device /dev:/dev \
            -e DISPLAY=":0.0" \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v `pwd`:/outside \
            $(IMAGE_NAME) /bin/bash

run:
	#xhost +
	-docker rm -f tempmon 2>/dev/null || :
	docker run -d --restart unless-stopped \
            --name tempmon \
            --privileged \
            -p 0.0.0.0:80:80 \
            --device /dev:/dev \
            -e DISPLAY=":0.0" \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            $(IMAGE_NAME)

