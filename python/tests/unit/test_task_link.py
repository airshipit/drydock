# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
'''Tests the functions for adding and retrieving task status links.'''
from drydock_provisioner.objects import TaskStatus


class TestTaskStatusLinks():

    def test_links_add(self):
        '''Add a link to a task status.'''
        ts = TaskStatus()

        relation = 'test'
        uri = 'http://foo.com/test'

        ts.add_link(relation, uri)

        assert relation in ts.links
        assert uri in ts.links.get(relation, [])

    def test_links_get_empty(self):
        '''Get links with an empty list.'''
        ts = TaskStatus()

        links = ts.get_links()

        assert len(links) == 0

        relation = 'test'
        uri = 'http://foo.com/test'

        ts.add_link(relation, uri)
        links = ts.get_links(relation='none')

        assert len(links) == 0

    def test_links_get_all(self):
        '''Get all links in a task status.'''
        ts = TaskStatus()

        relation = 'test'
        uri = 'http://foo.com/test'

        ts.add_link(relation, uri)
        links = ts.get_links()

        assert len(links) == 1
        assert uri in links

    def test_links_get_all_duplicate_relation(self):
        '''Get all links where a relation has multiple uris.'''
        ts = TaskStatus()

        relation = 'test'
        uri = 'http://foo.com/test'
        uri2 = 'http://baz.com/test'

        ts.add_link(relation, uri)
        ts.add_link(relation, uri2)

        links = ts.get_links()

        assert len(links) == 2
        assert uri in links
        assert uri2 in links

    def test_links_get_filter(self):
        '''Get links with a filter.'''
        ts = TaskStatus()

        relation = 'test'
        uri = 'http://foo.com/test'

        relation2 = 'test2'
        uri2 = 'http://baz.com/test'

        ts.add_link(relation, uri)
        ts.add_link(relation2, uri2)

        links = ts.get_links(relation=relation)

        assert len(links) == 1
        assert uri in links

        links = ts.get_links(relation=relation2)

        assert len(links) == 1
        assert uri2 in links

    def test_links_serialization(self):
        '''Check that task status serilization contains links correctly.'''
        ts = TaskStatus()

        relation = 'test'
        uri = 'http://bar.com'

        ts.set_message('foo')
        ts.set_reason('bar')
        ts.add_link(relation, uri)

        ts_dict = ts.to_dict()

        assert isinstance(ts_dict.get('links'), list)
        assert {'rel': relation, 'href': uri} in ts_dict.get('links', [])
