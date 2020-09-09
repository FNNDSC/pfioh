#!/bin/bash

set -ev
cd ..
git clone https://github.com/FNNDSC/ChRIS_ultron_backEnd.git
pushd pfioh/
docker build -t fnndsc/pfioh:latest .
popd
pushd ChRIS_ultron_backEnd/
docker build -t fnndsc/chris:dev -f Dockerfile_dev .
docker pull fnndsc/pfdcm
docker pull fnndsc/swarm
docker swarm init --advertise-addr 127.0.0.1
chmod -R 755 $(pwd)
mkdir -p FS/remote
chmod -R 777 FS
export STOREBASE=$(pwd)/FS/remote
docker-compose -f docker-compose_dev.yml up -d
docker-compose -f docker-compose_dev.yml exec chris_dev_db sh -c 'while ! mysqladmin -uroot -prootp status 2> /dev/null; do sleep 5; done;'
docker-compose -f docker-compose_dev.yml exec chris_dev_db mysql -uroot -prootp -e 'GRANT ALL PRIVILEGES ON *.* TO "chris"@"%"'
