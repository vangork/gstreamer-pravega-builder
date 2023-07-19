#!/bin/bash

#
# Copyright (c) Dell Inc., or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#

set -ex

ROOT_DIR=$(readlink -f $(dirname $0)/..)
RUST_JOBS=${RUST_JOBS:-4}
BASE_IMAGE=ubuntu:20.04

# Make sure to always have fresh base image.
docker pull ${BASE_IMAGE}

# Build pravega-prod image which includes the binaries for all applications.
DOCKER_BUILDKIT=1 docker build \
    -t pravega/pravega-pytorch \
    --build-arg RUST_JOBS=${RUST_JOBS} \
    --build-arg BASE_IMAGE=${BASE_IMAGE} \
    --build-arg HTTP_PROXY="http://172.17.0.1:19000" \
    --build-arg HTTPS_PROXY="http://172.17.0.1:19000" \
    --target prod \
    -f ${ROOT_DIR}/docker/Dockerfile \
    ${ROOT_DIR}
