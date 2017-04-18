#!/bin/bash
# Removes all stopped containers and eliminates all dangling images.

docker rm $(docker ps -q -f status=exited)
docker rmi `docker images | awk '{ print $3; }'`
