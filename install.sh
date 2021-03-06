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
libmagickwand-dev ufraw dcraw wget nginx

sudo pip install tornado tornadotools redis pillow Wand piexif
set +e

sed -e "s|\${root}|${SOURCE}|g" $SOURCE/cfg/example_supervisord.conf | sudo tee /etc/supervisor/conf.d/example_supervisord.conf > /dev/null
sed -e "s|\${static}|${SOURCE}|g" $SOURCE/cfg/example_nginx.conf | sudo tee /etc/nginx/conf.d/example_nginx.conf > /dev/null

sudo service supervisor restart
sudo service nginx restart

echo "DONE"
