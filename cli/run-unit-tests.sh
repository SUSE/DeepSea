#!/bin/bash

cd tests
docker build -t deepsea-cli .
cd ..

docker run --rm -ti -v `pwd`/..:/deepsea --net=host deepsea-cli $*
