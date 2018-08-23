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

import (
	"fmt"
	"os"
)

func main() {
	conf := parseConfig()

	// Indicates the help CLI flag was given
	if conf == nil {
		os.Exit(0)
	}

	if !conf.validate() {
		os.Exit(2)
	}

	var err error

	if conf.wrapExecutable != "" {
		err = reportExecution(conf)
	} else {
		err = reportMessage(conf)
	}

	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	fmt.Printf("Bootaction status posted.\n")
	os.Exit(0)
}

func reportExecution(conf *ClientConfig) error {
	url := renderURL(conf)

	msg, _ := newMessage("Bootaction starting execution.", false, "")
	err := msg.post(url, conf.bootactionKey)

	if err != nil {
		return fmt.Errorf("Error accessing API: %s", err)
	}

	result := executeAction(conf.wrapExecutable, conf.proxyEnvironment)

	if result {
		msg, _ = newMessage("Bootaction execution successful.", false, SUCCESS)
	} else {
		msg, _ = newMessage("Bootaction execution failed.", true, FAILURE)
	}

	err = msg.post(url, conf.bootactionKey)

	if err != nil {
		return fmt.Errorf("Error accessing API: %s", err)
	}

	return nil
}

func reportMessage(conf *ClientConfig) error {
	url := renderURL(conf)

	msg, err := newMessage(conf.message, conf.isError, conf.status)

	if err != nil {
		return fmt.Errorf("Error creating message: %s\n", err)
	}

	err = msg.post(url, conf.bootactionKey)

	if err != nil {
		return fmt.Errorf("Error accesing API: %s\n", err)
	}

	return nil
}

func renderURL(conf *ClientConfig) (fullURL string) {
	fullURL = fmt.Sprintf("%s/%s/", conf.apiURL, conf.bootactionID)
	return
}

func newMessageDetail(msg string, isError bool) (*BootactionDetail, error) {
	// isError defaults to false if nil
	if msg == "" {
		return nil, fmt.Errorf("Error creating MessageDetail, message string undefined.")
	}

	var msg_detail BootactionDetail

	msg_detail.Message = msg
	msg_detail.IsError = isError

	return &msg_detail, nil
}

func newMessage(msg string, isError bool, finalStatus string) (*BootactionMessage, error) {
	msg_detail, err := newMessageDetail(msg, isError)

	if err != nil {
		return nil, fmt.Errorf("Error creating Message: %s", err)
	}

	var message BootactionMessage

	message.Status = finalStatus
	message.Details = []BootactionDetail{*msg_detail}

	return &message, nil
}
