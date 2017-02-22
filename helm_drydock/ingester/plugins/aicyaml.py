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

#
# AIC YAML Ingester - This data ingester will consume a AIC YAML design
#					file 
# 	
import yaml
import logging

import helm_drydock.ingester.plugins.IngesterPlugin

class AicYamlIngester(IngesterPlugin):

	def __init__(self):
		super(AicYamlIngester, self).__init__()

	def get_name(self):
		return "aic_yaml"

	"""
	AIC YAML ingester params

	filename - Absolute path to the YAML file to ingest
	"""
	def ingest_data(self, **kwargs):
		if 'filename' in params:
			input_string = read_input_file(params['filename'])
			parsed_data = parse_input_data(input_string)
			processed_data = compute_effective_data(parsed_data)
		else:

			raise Exception('Missing parameter')
		
		return processed_data

	def read_input_file(self, filename):
		try:
			file = open(filename,'rt')
		except OSError as err:
			self.log.error("Error opening input file %s for ingestion: %s" % (filename, err))
			return {}


