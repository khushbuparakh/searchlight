# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import six

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging
# TODO(sjmc7): Figure this out better. The glance plugin uses the API
# policy module as the enforcer for property_utils
from oslo_policy import opts as oslo_policy_opts
from oslo_service import service as os_service

from searchlight.common import utils
from searchlight import i18n

LOG = logging.getLogger(__name__)
_ = i18n._
_LE = i18n._LE

listener_opts = [
    cfg.IntOpt('workers',
               default=1,
               min=1,
               help='Number of workers for notification service. A single '
               'notification agent is enabled by default.'),
]

CONF = cfg.CONF
oslo_policy_opts._register(CONF)
CONF.register_opts(listener_opts, group="listener")


class NotificationEndpoint(object):

    def __init__(self, plugins):
        self.plugins = plugins
        self.notification_target_map = {}
        for plugin_type, plugin in six.iteritems(self.plugins):
            try:
                handler = plugin.obj.get_notification_handler()
                event_list = handler.get_notification_supported_events()
                for event in event_list:
                    LOG.debug("Registering event '%s' for plugin '%s'",
                              event, plugin.name)
                    # Add this plugin to the list of handlers for this event
                    # type, creating that list if necessary
                    self.notification_target_map.setdefault(
                        event.lower(), []).append(plugin.obj)
            except Exception as e:
                LOG.error(_LE("Failed to retrieve supported notification"
                              " events from search plugins "
                              "%(ext)s: %(e)s") %
                          {'ext': plugin.name, 'e': e})

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        event_type_l = event_type.lower()
        # The notification map contains a list of plugins for each event
        # type subscribed to
        for plugin in self.notification_target_map.get(event_type_l, []):
            LOG.debug("Processing event '%s' with plugin '%s'",
                      event_type_l, plugin.name)
            handler = plugin.get_notification_handler()
            handler.process(
                ctxt,
                publisher_id,
                event_type,
                payload,
                metadata)


class ListenerService(os_service.Service):
    def __init__(self, *args, **kwargs):
        super(ListenerService, self).__init__(*args, **kwargs)
        self.plugins = utils.get_search_plugins()
        self.listeners = []
        self.topics_exchanges_set = self.topics_and_exchanges()

    def topics_and_exchanges(self):
        topics_exchanges = set()
        for plugin_type, plugin in six.iteritems(self.plugins):
            try:
                handler = plugin.obj.get_notification_handler()
                topic_exchanges = handler.get_notification_topics_exchanges()
                for plugin_topic in topic_exchanges:
                    if isinstance(plugin_topic, basestring):
                        raise Exception(
                            _LE("Plugin %s should return a list of topic"
                                "exchange pairs") % plugin.__class__.__name__)
                    topics_exchanges.add(plugin_topic)
            except Exception as e:
                LOG.error(_LE("Failed to retrieve notification topic(s)"
                              " and exchanges from search plugin "
                              "%(ext)s: %(e)s") %
                          {'ext': plugin.name, 'e': e})

        return topics_exchanges

    def start(self):
        super(ListenerService, self).start()
        transport = oslo_messaging.get_transport(CONF)
        targets = [
            oslo_messaging.Target(topic=pl_topic, exchange=pl_exchange)
            for pl_topic, pl_exchange in self.topics_exchanges_set
        ]
        endpoints = [
            NotificationEndpoint(self.plugins)
        ]
        listener = oslo_messaging.get_notification_listener(
            transport,
            targets,
            endpoints,
            executor='threading')

        listener.start()
        self.listeners.append(listener)

    def stop(self):
        for listener in self.listeners:
            listener.stop()
            listener.wait()
        super(ListenerService, self).stop()
