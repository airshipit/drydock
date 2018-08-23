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

// Tests for the baclient

package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/ioutil"
	mrand "math/rand"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestPostIncompleteMessage(t *testing.T) {
	var conf ClientConfig

	bootactionID := generateID()
	bootactionKey := generateKey()

	ts := buildTestServer(t, bootactionID, bootactionKey, "")
	defer ts.Close()

	conf.apiURL = fmt.Sprintf("%s/api/v1.0/bootaction", ts.URL)
	conf.bootactionID = bootactionID
	conf.bootactionKey = bootactionKey
	conf.message = "Testing 1 2 3"
	conf.isError = false

	err := reportMessage(&conf)

	if err != nil {
		t.Error(fmt.Sprintf("%s", err))
	}

}

func TestPostSuccessMessage(t *testing.T) {
	var conf ClientConfig

	bootactionID := generateID()
	bootactionKey := generateKey()

	ts := buildTestServer(t, bootactionID, bootactionKey, SUCCESS)
	defer ts.Close()

	conf.apiURL = fmt.Sprintf("%s/api/v1.0/bootaction", ts.URL)
	conf.bootactionID = bootactionID
	conf.bootactionKey = bootactionKey
	conf.message = "Testing 1 2 3"
	conf.isError = false
	conf.status = SUCCESS

	err := reportMessage(&conf)

	if err != nil {
		t.Error(fmt.Sprintf("%s", err))
	}
}

func TestPostFailureMessage(t *testing.T) {
	var conf ClientConfig

	bootactionID := generateID()
	bootactionKey := generateKey()

	ts := buildTestServer(t, bootactionID, bootactionKey, FAILURE)
	defer ts.Close()

	conf.apiURL = fmt.Sprintf("%s/api/v1.0/bootaction", ts.URL)
	conf.bootactionID = bootactionID
	conf.bootactionKey = bootactionKey
	conf.message = "Testing 1 2 3"
	conf.isError = true
	conf.status = FAILURE

	err := reportMessage(&conf)

	if err != nil {
		t.Error(fmt.Sprintf("%s", err))
	}
}

func TestPostSuccessExec(t *testing.T) {
	var conf ClientConfig

	bootactionID := generateID()
	bootactionKey := generateKey()

	ts := buildTestServer(t, bootactionID, bootactionKey, SUCCESS)
	defer ts.Close()

	conf.apiURL = fmt.Sprintf("%s/api/v1.0/bootaction", ts.URL)
	conf.bootactionID = bootactionID
	conf.bootactionKey = bootactionKey
	conf.wrapExecutable = "/bin/true"

	err := reportExecution(&conf)

	if err != nil {
		t.Error(fmt.Sprintf("%s", err))
	}
}

func TestPostFailureExec(t *testing.T) {
	var conf ClientConfig

	bootactionID := generateID()
	bootactionKey := generateKey()

	ts := buildTestServer(t, bootactionID, bootactionKey, FAILURE)
	defer ts.Close()

	conf.apiURL = fmt.Sprintf("%s/api/v1.0/bootaction", ts.URL)
	conf.bootactionID = bootactionID
	conf.bootactionKey = bootactionKey
	conf.wrapExecutable = "/bin/false"

	err := reportExecution(&conf)

	if err != nil {
		t.Error(fmt.Sprintf("%s", err))
	}
}

func generateID() string {
	// In order to stay within the Go stdlib and because real randomness here
	// isn't that valuable, just pick one of a few hardcoded ulids
	var ulidPool [5]string = [5]string{
		"01CP38QN33KZ5E2MZBC0S7PJHR",
		"01CP393Q44NW9TFVT1W8QTY2PP",
		"01CP39489G7SRNJX6G1E61P4X5",
		"01CP394JQEEH6127FCQVB4TBKY",
		"01CP394TFYMH38VSM4JNJZHM9Y",
	}

	selector := mrand.Int31n(5)
	return ulidPool[selector]
}

func generateKey() string {
	key := make([]byte, 32)
	_, _ = rand.Read(key)

	keyHex := make([]byte, hex.EncodedLen(len(key)))
	hex.Encode(keyHex, key)

	return string(keyHex)
}

func buildTestServer(t *testing.T, bootactionID string, bootactionKey string, expectedResult string) *httptest.Server {
	hf := func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Logf("Request used method %s.\n", r.Method)
			w.WriteHeader(405)
			return
		}

		contentType := r.Header.Get("Content-Type")

		if contentType != "application/json" {
			t.Logf("Request had content type '%s'\n", contentType)
			w.WriteHeader(415)
			return
		}

		reqKey := r.Header.Get("X-Bootaction-Key")

		if reqKey != bootactionKey {
			t.Logf("Request contained 'X-Bootaction-Key': %s\n", reqKey)
			w.WriteHeader(403)
			return
		}

		if !strings.Contains(r.URL.Path, bootactionID) {
			t.Logf("Requested URL path '%s' missing bootactionID\n", r.URL.Path)
			w.WriteHeader(404)
			return
		}

		reqBody, err := ioutil.ReadAll(r.Body)

		if err != nil {
			t.Logf("Error reading test request: %s\n", err)
			w.WriteHeader(400)
			return
		}

		var message BootactionMessage

		err = json.Unmarshal(reqBody, &message)

		if err != nil {
			t.Logf("Error parsing test request: %s\n", err)
			w.WriteHeader(400)
			return
		}

		if message.Status != "" && message.Status != expectedResult {
			t.Logf("Did not receive expected result, instead received '%s'\n", message.Status)
			w.WriteHeader(400)
			return
		}

		t.Logf("Handled request: %s - %s\n", r.Method, r.URL.Path)
		t.Logf("Key: %s\n", reqKey)
		t.Logf("Body:\n %s\n", reqBody)
		w.WriteHeader(201)
		return
	}

	ts := httptest.NewServer(http.HandlerFunc(hf))

	return ts
}
