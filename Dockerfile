FROM arm32v6/python:2-alpine

RUN apk --no-cache --update add bash curl

COPY adafruit-pitft.sh /
RUN /adafruit-pitft.sh 

# Install flask (for the REST API server)
RUN pip install Flask

# Copy over the source code
COPY tempmon.py /
WORKDIR /

# Run the daemon
CMD python tempmon.py

