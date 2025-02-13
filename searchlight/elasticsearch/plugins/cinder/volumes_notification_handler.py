# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
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

import cinderclient.exceptions
from oslo_log import log as logging

from searchlight.elasticsearch.plugins import base
from searchlight.elasticsearch.plugins.cinder import serialize_cinder_volume
from searchlight import i18n


LOG = logging.getLogger(__name__)
_LW = i18n._LW
_LE = i18n._LE


class VolumeHandler(base.NotificationBase):
    """Handles cinder volume notifications. These can come as a result of
    a user action (like a create, delete, metadata edit etc) or as a result of
    periodic auditing notifications cinder sends
    """

    @classmethod
    def _get_notification_exchanges(cls):
        return ['cinder']

    def get_event_handlers(self):
        return {
            'volume.update.end': self.create_or_update,
            'volume.create.end': self.create_or_update,
            'volume.delete.end': self.delete,
            # TODO(sjmc7) These could be implemented as scripted updates
            'volume.attach.end': self.create_or_update,
            'volume.detach.end': self.create_or_update,
        }

    def create_or_update(self, payload, timestamp):
        volume_id = payload['volume_id']
        LOG.debug("Updating cinder volume information for %s", volume_id)

        try:
            payload = serialize_cinder_volume(volume_id)
            version = self.get_version(payload, timestamp)
            self.index_helper.save_document(payload, version=version)
        except cinderclient.exceptions.NotFound:
            LOG.warning(_LW("Volume %s not found; deleting") % volume_id)
            self.delete(payload, timestamp)

    def delete(self, payload, timestamp):
        volume_id = payload['volume_id']
        LOG.debug("Deleting cinder volume information for %s", volume_id)
        if not volume_id:
            return

        try:
            self.index_helper.delete_document({'_id': volume_id})
        except Exception as exc:
            LOG.error(_LE(
                'Error deleting volume %(volume_id)s '
                'from index. Error: %(exc)s') %
                {'volume_id': volume_id, 'exc': exc})
