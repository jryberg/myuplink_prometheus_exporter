#!/bin/bash
COMPONENT=${PWD##*/}
docker build --rm . -t ${COMPONENT}
