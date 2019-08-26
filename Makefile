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

BUILD_DIR       	:= $(shell mkdir -p build && mktemp -d -p build)
DOCKER_REGISTRY 	?= quay.io
IMAGE_NAME      	?= drydock
IMAGE_PREFIX    	?= airshipit
IMAGE_TAG       	?= dev
HELM            	:= $(shell realpath $(BUILD_DIR))/helm
UBUNTU_BASE_IMAGE	?=
PROXY           	?= http://proxy.foo.com:8000
NO_PROXY        	?= localhost,127.0.0.1,.svc.cluster.local
USE_PROXY       	?= false
PUSH_IMAGE      	?= false
# use this variable for image labels added in internal build process
LABEL           	?= org.airshipit.build=community
COMMIT          	?= $(shell git rev-parse HEAD)
IMAGE           	?= ${DOCKER_REGISTRY}/${IMAGE_PREFIX}/${IMAGE_NAME}:${IMAGE_TAG}
GO_BUILDER      	?= docker.io/golang:1.10-stretch

export

# Build all docker images for this project
images: build_drydock

# Run an image locally and exercise simple tests
run_images: run_drydock

# Run tests
tests: pep8 security docs unit_tests test_baclient

# Install external (not managed by tox/pip) dependencies
external_dep: requirements-host.txt requirements-host-test.txt
	sudo ./hostdeps.sh
	touch external_dep

# Run unit and Postgres integration tests in coverage mode
coverage_test: build_drydock
	tox -re cover

# Run just unit tests
unit_tests: external_dep
	tox -re py35 $(TESTS)

# Run just DB integration tests
db_integration_tests: external_dep
	tox -re integration $(TESTS)

# Freeze full set of Python requirements
req_freeze:
	tox -re freeze

# Run the drydock container and exercise simple tests
run_drydock: build_drydock
	tools/drydock_image_run.sh

# It seems CICD expects the target 'drydock' to
# build the chart
drydock: charts

# Create tgz of the chart
charts: helm-init
	$(HELM) dep up charts/drydock
	$(HELM) package charts/drydock

# Perform Linting
lint: pep8 helm_lint

# Dry run templating of chart
dry-run: helm-init
	$(HELM) template --set manifests.secret_ssh_key=true --set conf.ssh.private_key=foo charts/drydock

# Initialize local helm config
helm-init: helm-install
	tools/helm_tk.sh $(HELM)

# Install helm binary
helm-install:
	tools/helm_install.sh $(HELM)

# Make targets intended for use by the primary targets above.

build_drydock: external_dep build_baclient
	export; tools/drydock_image_build.sh
ifeq ($(PUSH_IMAGE), true)
	docker push $(IMAGE)
endif

# Make target for building bootaction signal client
build_baclient: external_dep
	docker run -tv $(shell realpath go):/work -v $(shell realpath $(BUILD_DIR)):/build -e GOPATH=/work $(GO_BUILDER)  go build -o /build/baclient baclient

# Make target for testing bootaction signal client
test_baclient: external_dep
	docker run -tv $(shell realpath go):/work -e GOPATH=/work $(GO_BUILDER)  go test -v baclient

docs: clean drydock_docs

security: external_dep
	tox -e bandit

drydock_docs: external_dep render_diagrams genpolicy genconfig
	tox -e docs

render_diagrams:
	plantuml -v -tpng -o ../source/images doc/diagrams/*.uml

genpolicy:
	tox -e genpolicy

genconfig:
	tox -e genconfig

clean:
	rm -rf build
	rm -rf doc/build
	rm -rf charts/drydock/charts
	rm -rf charts/drydock/requirements.lock

pep8: external_dep
	tox -e pep8

helm_lint: helm-init
	$(HELM) lint charts/drydock

.PHONY: build_baclient build_drydock charts clean coverage_test \
  db_integration_tests docs drydock drydock_docs dry-run genconfig \
  genpolicy helm-init helm-install helm_lint images lint pep8 \
  render_diagrams req_freeze run_drydock run_images security \
  test_baclient tests unit_tests
