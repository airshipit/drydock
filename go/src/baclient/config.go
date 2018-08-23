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

package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strings"
)

func parseConfig() *ClientConfig {
	var clientConfig ClientConfig

	parseFlagConfig(&clientConfig)

	if clientConfig.showHelp {
		flag.PrintDefaults()
		return nil
	}

	parseEnvConfig(&clientConfig)

	if clientConfig.bootactionKey == "" {
		if clientConfig.bootactionKeyPath != "" {
			clientConfig.bootactionKey, _ = readKeyFile(clientConfig.bootactionKeyPath)
		}
	}

	return &clientConfig
}

func readKeyFile(keyPath string) (string, error) {
	keyFile, err := os.Open(keyPath)
	defer keyFile.Close()

	if err == nil {
		var keyString string

		bufReader := bufio.NewReader(keyFile)

		keyString, err = bufReader.ReadString('\n')

		if err != nil {
			return "", fmt.Errorf("Error reading key file: %s", err)
		} else {
			keyString = strings.Trim(keyString, "\n")
			return keyString, nil
		}
	} else {
		return "", fmt.Errorf("Error opening key file: %s", err)
	}
}

func parseFlagConfig(clientConfig *ClientConfig) {
	// If neither 's' or 'f' are specified, the API call will omit the 'status' field
	success := flag.Bool("s", false, "Does this message indicate bootaction success.")
	failure := flag.Bool("f", false, "Does this message indicate bootaction failure.")

	if *failure {
		clientConfig.status = FAILURE
	} else if *success {
		clientConfig.status = SUCCESS
	}

	flag.BoolVar(&clientConfig.showHelp, "h", false, "Show help and exit")
	flag.BoolVar(&clientConfig.isError, "e", false, "Does this message indicate error")
	flag.BoolVar(&clientConfig.proxyEnvironment, "np", false, "When wrapping an executable, should proxying the environment be disabled.")

	flag.StringVar(&clientConfig.apiURL, "url", "", "Drydock API URL")
	flag.StringVar(&clientConfig.bootactionID, "id", "", "Bootaction ID")
	flag.StringVar(&clientConfig.bootactionKey, "key", "", "Bootaction ID")
	flag.StringVar(&clientConfig.bootactionKeyPath, "keyfile", "", "Absolute path to a file containing the API key")
	flag.StringVar(&clientConfig.message, "msg", "", "The detail message to record for the bootaction")
	flag.StringVar(&clientConfig.wrapExecutable, "exec", "", "The absolute path to an executable to run and report result.")

	flag.Parse()
}

func parseEnvConfig(clientConfig *ClientConfig) {
	// for security, support reading the bootaction key from the environment
	baKey := os.Getenv("BOOTACTION_KEY")

	if baKey != "" {
		clientConfig.bootactionKey = baKey
	}
}

func (clientConfig *ClientConfig) validate() bool {
	valid := true

	if clientConfig.bootactionID == "" {
		valid = false
		fmt.Printf("No Bootaction ID specified.\n")
	}

	if clientConfig.bootactionKey == "" && clientConfig.bootactionKeyPath == "" {
		valid = false
		fmt.Printf("No Bootaction Key is specified.\n")
	}

	if clientConfig.message == "" {
		valid = false
		fmt.Printf("Status message required.\n")
	}

	return valid
}
