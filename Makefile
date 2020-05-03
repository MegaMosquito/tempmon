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

# Remove the local container image
clean:
	-docker rm -f $(IMAGE_NAME) 2>/dev/null || :
	-docker rmi -f $(IMAGE_NAME) 2>/dev/null || :

# ----------------------------------------------------------------------------

dev:
	#xhost +
	-docker rm -f tempmon 2>/dev/null || :
	docker run -it -p 0.0.0.0:8000:6543 \
            --name tempmon --privileged --restart unless-stopped \
            --device /dev:/dev \
            -e DISPLAY=":0.0" \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v `pwd`:/outside \
            $(IMAGE_NAME) /bin/bash

run:
	#xhost +
	-docker rm -f tempmon 2>/dev/null || :
	docker run -d -p 0.0.0.0:80:6543 \
            --name tempmon --privileged --restart unless-stopped \
            --device /dev:/dev \
            -e DISPLAY=":0.0" \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            $(IMAGE_NAME)


