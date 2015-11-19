#!/bin/bash

cd $(dirname $0)

git fetch -q

BRANCH=$(git branch | awk '/^[*]/{print$2}')

if [ "$BRANCH" -ne "master" ]; then
    git checkout master
fi

git pull -q origin master

./muxer/muxer_service.init.sh restart
