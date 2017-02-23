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
#                   file 
#   
import yaml
import logging

import helm_drydock.model as model
from helm_drydock.ingester.plugins import IngesterPlugin

class AicYamlIngester(IngesterPlugin):

    kind_map = {
        "Region": model.Site,
        "NetworkLink": model.NetworkLink,
        "HardwareProfile": model.HardwareProfile,
        "Network": model.Network,
        "HostProfile": model.HostProfile,
        "BaremetalNode": model.BaremetalNode,
    }

    def __init__(self):
        super(AicYamlIngester, self).__init__()

    def get_name(self):
        return "aic_yaml"

    """
    AIC YAML ingester params

    filenames - Array of absolute path to the YAML files to ingest

    returns an array of objects from helm_drydock.model

    """
    def ingest_data(self, **kwargs):
        if 'filenames' in kwargs:
            # TODO validate filenames is array
            for f in kwargs.get('filenames'):
                try:
                    file = open(f,'rt')
                    contents = file.read()
                    file.close()
                except OSError as err:
                    self.log.error(
                        "Error opening input file %s for ingestion: %s" 
                        % (filename, err))
                    continue
        
                try:
                    parsed_data = yaml.load_all(contents)
                except yaml.YAMLError as err:
                    self.log.error("Error parsing YAML in %s: %s" % (f, err))
                    continue

                models = []
                for d in parsed_data:
                    kind = d.get('kind', '')
                    if kind != '':
                        if kind in AicYamlIngester.kind_map:
                            try:
                                model = AicYamlIngester.kind_map[kind](**d)
                                models.append(model)
                            except Exception as err:
                                self.log.error("Error building model %s: %s" 
                                    % (kind, str(err)))
                        else:
                            self.log.error(
                                "Error processing document, unknown kind %s" 
                                % (kind))
                            continue
                    else:
                        self.log.error(
                            "Error processing document in %s, no kind field"
                            % (f))
                        continue

                return models
        else:
            raise ValueError('Missing parameter "filename"')
        
        return processed_data
        


