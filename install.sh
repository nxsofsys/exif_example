#!/bin/bash

SOURCE=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $SOURCE

echo "Please wait..."
set -e
sudo apt-get install -qq --assume-yes \
supervisor redis-server curl libcurl4-openssl-dev \
python-pip python-dev make build-essential \
libtiff5-dev libjpeg8-dev zlib1g-dev \
libfreetype6-dev liblcms2-dev \
libwebp-dev tcl8.6-dev tk8.6-dev python-tk \
libexiv2-dev libgexiv2-2 gir1.2-gexiv2-0.10 \
libmagickwand-dev ufraw dcraw wget

sudo pip install tornado tornadotools redis pillow Wand piexif
set +e

sudo sed -e "s|\${root}|${SOURCE}|g" $SOURCE/cfg/example_supervisord.conf > /etc/supervisor/conf.d/example_supervisord.conf
sudo service supervisor restart

sudo sed -e "s|\${static}|${SOURCE}|g" $SOURCE/cfg/example_nginx.conf > /etc/nginx/conf.d/example_nginx.conf
sudo service nginx restart

echo "DONE"
