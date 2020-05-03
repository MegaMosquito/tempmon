FROM raspbian/stretch

RUN apt update && apt install -y \
  python \
  python-dev \
  python-pip \
  libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsmpeg-dev \
  libsdl1.2-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
  libtiff5-dev libx11-6 libx11-dev fluid-soundfont-gm timgm6mb-soundfont \
  xfonts-base xfonts-100dpi xfonts-75dpi \
  fontconfig fonts-freefont-ttf libfreetype6-dev \
  git \
  bash \
  curl \
  jq

# Grab Adafruit BMP library source, then build and install
WORKDIR /opt
RUN git clone https://github.com/sunfounder/Adafruit_Python_BMP.git
WORKDIR /opt/Adafruit_Python_BMP
RUN python setup.py install

# Install other dependencies
# RUN pip install adafruit-blinka Flask pygame
RUN pip install RPI.GPIO Flask pygame

# Copy over my code
WORKDIR /
COPY tempmon.py /

# Default command is to launch the daemon
CMD python tempmon.py

