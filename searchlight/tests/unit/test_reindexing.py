# (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from elasticsearch import exceptions as es_exc
from searchlight.elasticsearch.plugins import utils as plugin_utils
from searchlight.tests import utils as test_utils


class TestReindexingUtils(test_utils.BaseTestCase):
    def test_reindex(self):
        src = 'sl-old'
        dst = 'sl-new'
        single = ['OS::Neutron::Net']
        mult = ['OS::Neutron::Net', 'OS::Nova::Server', 'OS::Glance::Image']
        reindex_name = 'searchlight.elasticsearch.plugins.utils.helper_reindex'

        expected_single = {'query': {
                           'filtered': {
                               'filter': {
                                   'terms': {
                                       '_type': single}
                               }
                           }}, 'version': 'true'}
        expected_mult = {'query': {
                         'filtered': {
                             'filter': {
                                 'terms': {
                                     '_type': mult}
                             }
                         }}, 'version': 'true'}

        # Set up the ES mock.
        mock_engine = mock.Mock()
        with mock.patch('searchlight.elasticsearch.get_api') as mock_api:
            with mock.patch(reindex_name) as mock_reindex:
                # Plug in the ES mock.
                mock_api.return_value = mock_engine

                # Test #1: Reindex a single index.
                plugin_utils.reindex(src, dst, single)
                mock_api.assert_called_with()
                mock_reindex.assert_called_with(client=mock_engine,
                                                source_index=src,
                                                target_index=dst,
                                                query=expected_single)

                # Test #2: Reindex multiple indexes.
                plugin_utils.reindex(src, dst, mult)
                mock_reindex.assert_called_with(client=mock_engine,
                                                source_index=src,
                                                target_index=dst,
                                                query=expected_mult)

    def test_create_new_index(self):
        # Regex for matching the index name. The index name is the group
        # group name appended with a time stmap. The format for the
        # timestamp is defined in elasitcsearch.plugins.utils and is
        # defined as:
        #     [4 digit Year] [2 digit Month] [2 digit Day] [2 digit Hour]
        #     [2 digit Minutes] [2 digit Seconds]
        # We want to search for this pattern exactly, which is why we are
        # specifying "^" and "$" in the Regex. We elected to make the unit
        # test more complicated, rather than artificially wrap datetime
        # functionality in the code just for the tests.
        TS_FORMAT = '\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}$'
        group = 'searchlight'

        # Set up the ES mock.
        mock_engine = mock.Mock()
        with mock.patch('searchlight.elasticsearch.get_api') as mock_api:
            # Plug in the ES mock.
            mock_api.return_value = mock_engine

            # Test #1: Create a new index.
            index_name = plugin_utils.create_new_index(group)

            self.assertRegexpMatches(index_name, group + '-' + TS_FORMAT)
            mock_api.assert_called_with()
            mock_engine.indices.create.assert_called_with(index=index_name)

    def test_setup_alias(self):
        ndx = 'sl'
        ndx_s = 'sl-s'
        ndx_l = 'sl-l'
        body = {'actions': [{'add': {'index': ndx, 'alias': ndx_l}}]}

        # Set up the ES mock.
        mock_engine = mock.Mock()
        with mock.patch('searchlight.elasticsearch.get_api') as mock_api:
            # Plug in the ES mock.
            mock_api.return_value = mock_engine

            # Test #1: No search alias, no listener alias.
            mock_engine.indices.exists_alias.side_effect = [False, False]
            plugin_utils.setup_alias(ndx, ndx_s, ndx_l)
            calls = [mock.call(index=ndx, name=ndx_s),
                     mock.call(index=ndx, name=ndx_l)]
            mock_engine.indices.put_alias.assert_has_calls(calls)
            mock_engine.indices.update_aliases.assert_not_called()
            mock_api.assert_called_with()

            # Test #2: No search alias, existing listener alias.
            mock_engine.reset_mock()
            mock_engine.indices.exists_alias.side_effect = [False, True]
            plugin_utils.setup_alias(ndx, ndx_s, ndx_l)
            mock_engine.indices.put_alias.assert_called_once_with(
                index=ndx, name=ndx_s)
            mock_engine.indices.update_aliases.assert_called_with(body=body)

            # Test #3: Existing search alias, existing listener alias.
            mock_engine.reset_mock()
            mock_engine.indices.exists_alias.side_effect = [True, True]
            plugin_utils.setup_alias(ndx, ndx_s, ndx_l)
            mock_engine.indices.put_aliases.assert_not_called()
            mock_engine.indices.update_aliases.assert_called_with(body=body)

            # Test #4: Exception while creating search alias
            mock_engine.reset_mock()
            mock_engine.indices.exists_alias.side_effect = [False]
            mock_engine.indices.put_alias.side_effect = [TypeError]
            self.assertRaises(TypeError, plugin_utils.setup_alias,
                              index_name=ndx, alias_search=ndx_s,
                              alias_listener=ndx_l)
            mock_engine.indices.delete.assert_called_once_with(index=ndx)

            # Test #5: Exception while creating listener alias
            mock_engine.reset_mock()
            mock_engine.indices.exists_alias.side_effect = [True, False]
            mock_engine.indices.put_alias.side_effect = [TypeError]
            self.assertRaises(TypeError, plugin_utils.setup_alias,
                              index_name=ndx, alias_search=ndx_s,
                              alias_listener=ndx_l)
            mock_engine.indices.delete.assert_called_once_with(index=ndx)

    def test_alias_search_update(self):
        ndx = 'sl-search'
        old_ndx = 'sl-old'
        new_ndx = 'sl-new'
        alias = {old_ndx: {'aliases': {ndx: {}}}}

        # Set up the ES mock.
        mock_engine = mock.Mock()
        with mock.patch('searchlight.elasticsearch.get_api') as mock_api:
            # Plug in the ES mock.
            mock_api.return_value = mock_engine

            # Test #1: Existing search alias, different index.
            mock_engine.indices.get_alias.return_value = alias

            index = plugin_utils.alias_search_update(ndx, new_ndx)
            body = {
                'actions': [{'remove': {'index': old_ndx, 'alias': ndx}},
                            {'add': {'index': new_ndx, 'alias': ndx}}]}
            mock_engine.indices.update_aliases.assert_called_once_with(body)
            self.assertEqual(index, old_ndx)
            mock_api.assert_called_with()

            # Test #2: Existing search alias, indexes are the same.
            mock_engine.reset_mock()
            mock_engine.indices.get_alias.return_value = alias

            index = plugin_utils.alias_search_update(ndx, old_ndx)
            mock_engine.indices.update_aliases.assert_not_called()
            self.assertIsNone(index)

            # Test #3: No index.
            mock_engine.reset_mock()

            index = plugin_utils.alias_search_update(ndx, None)
            self.assertIsNone(index)
            mock_engine.indices.get_alias.assert_not_called()
            mock_engine.indices.update_aliases.assert_not_called()

            # Test #4: Alias update failure.
            mock_engine.reset_mock()
            mock_engine.indices.get_alias.return_value = alias
            mock_engine.indices.update_aliases.side_effect = [TypeError]

            self.assertRaises(TypeError, plugin_utils.alias_search_update,
                              alias_search=ndx, index_name=new_ndx)

            # Test #5: No search alias.
            mock_engine.reset_mock()
            mock_engine.indices.get_alias.side_effect = es_exc.NotFoundError
            mock_engine.indices.update_aliases.side_effect = [None]

            index = plugin_utils.alias_search_update(ndx, new_ndx)
            body = {'actions': [{'add': {'index': new_ndx, 'alias': ndx}}]}
            mock_engine.indices.update_aliases.assert_called_once_with(body)
            self.assertIsNone(index)

    def test_alias_listener_update(self):
        ndx = 'sl-listener'
        old_ndx = 'sl-old'

        # Set up the ES mock.
        mock_engine = mock.Mock()
        with mock.patch('searchlight.elasticsearch.get_api') as mock_api:
            # Plug in the ES mock.
            mock_api.return_value = mock_engine

            # Test #1: Update the existing index.
            plugin_utils.alias_listener_update(ndx, old_ndx)

            body = {'actions': [{'remove': {'index': old_ndx, 'alias': ndx}}]}
            mock_engine.indices.update_aliases.assert_called_once_with(
                ignore=404, body=body)
            mock_engine.indices.delete.assert_called_once_with(ignore=404,
                                                               index=old_ndx)
            mock_api.assert_called_with()

            # Test #2: Index delete failure.
            mock_engine.reset_mock()
            mock_engine.indices.delete.side_effect = [Exception]

            plugin_utils.alias_listener_update(ndx, old_ndx)
            mock_engine.indices.update_aliases.assert_called_once_with(
                ignore=404, body=body)

            # Test #3: Alias update failure.
            mock_engine.reset_mock()
            mock_engine.indices.update_aliases.side_effect = [Exception]

            plugin_utils.alias_listener_update(ndx, old_ndx)
            mock_engine.indices.delete.assert_not_called()

    def test_alias_error_cleanup(self):
        single = {'g': 'ndx'}
        multiple = {'g1': 'ndx1', 'g2': 'ndx2', 'g3': 'ndx3'}

        # Set up the ES mock.
        mock_engine = mock.Mock()
        with mock.patch('searchlight.elasticsearch.get_api') as mock_api:
            # Plug in the ES mock.
            mock_api.return_value = mock_engine

            # Test #1: Cleanup a single index.
            plugin_utils.alias_error_cleanup(single)
            mock_engine.indices.delete.assert_called_once_with(ignore=404,
                                                               index='ndx')
            mock_api.assert_called_with()

            # Test #2: Cleanup multiple indexes.
            mock_engine.reset_mock()
            plugin_utils.alias_error_cleanup(multiple)
            calls = [mock.call(ignore=404, index='ndx1'),
                     mock.call(ignore=404, index='ndx2'),
                     mock.call(ignore=404, index='ndx3')]
            mock_engine.indices.delete.assert_has_calls(calls, any_order=True)

            # Test #3: Cleanup multiple indexes with an error.
            mock_engine.reset_mock()
            mock_engine.indices.delete.side_effect = [None, Exception, None]

            plugin_utils.alias_error_cleanup(multiple)
            calls = [mock.call(ignore=404, index='ndx1'),
                     mock.call(ignore=404, index='ndx2'),
                     mock.call(ignore=404, index='ndx3')]
            mock_engine.indices.delete.assert_has_calls(calls, any_order=True)
