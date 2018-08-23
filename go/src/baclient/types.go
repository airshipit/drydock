// Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// This is a CLI for interacting with the Airship-Drydock Bootaction Signal
// API

package main

const (
	SUCCESS = "success"
	FAILURE = "failure"
)

type ClientConfig struct {
	apiURL            string
	bootactionID      string
	bootactionKey     string
	bootactionKeyPath string
	message           string
	isError           bool
	status            string
	wrapExecutable    string
	proxyEnvironment  bool
	showHelp          bool
}

type BootactionMessage struct {
	Status  string             `json:"status,omitempty"`
	Details []BootactionDetail `json:"details"`
}

type BootactionDetail struct {
	Message string `json:"message"`
	IsError bool   `json:"error"`
}
