# Web UI for my indoor/outdoortemperature monitor

# ----------------------------------------------------------------------------

IMAGE_NAME_MASTER := 'ibmosquito/tempmon_master:1.0.0'
IMAGE_NAME_SLAVE  := 'ibmosquito/tempmon_slave:1.0.0'

all: build run

# Build the docker containers
build:
	docker build -t $(IMAGE_NAME_MASTER) -f ./Dockerfile.master .
	docker build -t $(IMAGE_NAME_SLAVE) -f ./Dockerfile.slave .

# Push the docker containers to DockerHub
push:
	docker push $(IMAGE_NAME_MASTER)
	docker push $(IMAGE_NAME_SLAVE)

# Test local temperature REST API
test:
	curl -sS http://localhost:80/temp-C | jq .

# Remove the local container image
clean:
	-docker rm -f $(IMAGE_NAME) 2>/dev/null || :
	-docker rmi -f $(IMAGE_NAME) 2>/dev/null || :

# ----------------------------------------------------------------------------

dev:
	env DISPLAY=:0.0 xhost +
	sudo rm -f core
	-docker rm -f tempmon 2>/dev/null || :
	docker run -it \
            --name tempmon \
            --privileged \
            -p 0.0.0.0:80:80 \
            --device /dev:/dev \
            -e MASTER="yes" \
            -e SLAVE_IP="192.168.123.96" \
            -e DISPLAY=":0.0" \
            -e TZ='America/Los_Angeles' \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v ~/.Xauthority:/root/.Xauthority \
            -v `pwd`:/outside \
            $(IMAGE_NAME_MASTER) /bin/bash

master:
	env DISPLAY=:0.0 xhost +
	-docker rm -f tempmon 2>/dev/null || :
	docker run -d --restart unless-stopped \
            --name tempmon \
            --privileged \
            -p 0.0.0.0:80:80 \
            --device /dev:/dev \
            -e MASTER="yes" \
            -e SLAVE_IP="192.168.123.96" \
            -e DISPLAY=":0.0" \
            -e TZ='America/Los_Angeles' \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v ~/.Xauthority:/root/.Xauthority \
            $(IMAGE_NAME_MASTER)

slave:
	-docker rm -f tempmon 2>/dev/null || :
	docker run -d --restart unless-stopped \
            --name tempmon \
            --privileged \
            -p 0.0.0.0:80:80 \
            --device /dev:/dev \
            $(IMAGE_NAME_SLAVE)

