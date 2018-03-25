# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

DOCKER_REGISTRY            ?= quay.io
IMAGE_NAME                 ?= drydock
IMAGE_PREFIX               ?= attcomdev
IMAGE_TAG                  ?= latest
HELM                       ?= helm
PROXY                      ?= http://one.proxy.att.com:8080
USE_PROXY                  ?= false
PUSH_IMAGE                 ?= false
LABEL                      ?= commit-id
IMAGE                      ?= ${DOCKER_REGISTRY}/${IMAGE_PREFIX}/${IMAGE_NAME}:${IMAGE_TAG}
export

# Build all docker images for this project
.PHONY: images
images: build_drydock

# Run an image locally and exercise simple tests
.PHONY: run_images
run_images: run_drydock

# Run tests
.PHONY: tests
tests: coverage_test

# Run unit and Postgres integration tests in coverage mode
.PHONY: coverage_test
coverage_test: build_drydock
	tox -e coverage

# Run the drydock container and exercise simple tests
.PHONY: run_drydock
run_drydock: build_drydock
	tools/drydock_image_run.sh

# Create tgz of the chart
.PHONY: charts
charts: clean
	$(HELM) dep up charts/drydock
	$(HELM) package charts/drydock

# Perform Linting
.PHONY: lint
lint: pep8 helm_lint

# Dry run templating of chart
.PHONY: dry-run
dry-run: clean
	tools/helm_tk.sh $(HELM)
	$(HELM) template --set manifests.secret_ssh_key=true --set conf.ssh.private_key=foo charts/drydock

# Make targets intended for use by the primary targets above.

.PHONY: build_drydock
build_drydock:
ifeq ($(USE_PROXY), true)
	docker build -t $(IMAGE) --label $(LABEL) -f images/drydock/Dockerfile . --build-arg http_proxy=$(PROXY) --build-arg https_proxy=$(PROXY)
else
	docker build -t $(IMAGE) --label $(LABEL) -f images/drydock/Dockerfile .
endif
ifeq ($(PUSH_IMAGE), true)
	docker push $(IMAGE)
endif

.PHONY: docs
docs: clean drydock_docs

.PHONY: drydock_docs
drydock_docs:
	tox -e docs

.PHONY: clean
clean:
	rm -rf build
	rm -rf docs/build
	rm -rf charts/drydock/charts
	rm -rf charts/drydock/requirements.lock

.PHONY: pep8
pep8:
	tox -e pep8

.PHONY: helm_lint
helm_lint: clean
	tools/helm_tk.sh $(HELM)
	$(HELM) lint charts/drydock
