# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

FROM python:3.10.13-alpine3.18 as builder

WORKDIR /build
RUN apk add gcc alpine-sdk
COPY requirements.txt ./
RUN pip install --no-cache-dir --target . -r requirements.txt

FROM python:3.10.13-alpine3.18
WORKDIR /opt/deye_inverter_mqtt
ADD src/*.py ./
ADD plugins ./plugins
ADD plugins/*.py ./plugins
COPY --from=builder /build/ ./

ENTRYPOINT [ "python", "./deye_docker_entrypoint.py" ]