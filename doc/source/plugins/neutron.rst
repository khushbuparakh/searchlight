..
    c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

********************
Neutron Plugin Guide
********************

Integration is provided via a plugin. There are multiple configuration
settings required for proper indexing and incremental updates. Some of the
settings are specified in Searchlight configuration files. Others are
provided in other service configuration files.

Searchlight Configuration
=========================

Searchlight resource configuration options are shown below with their
configuration file and default values.

See :ref:`searchlight-plugins` for common options with their default values,
general configuration information, and an example complete configuration.

.. note::

    Unless you are changing to a non-default value, you do not need to
    specify any of the following configuration options.

searchlight.conf
----------------

Plugin: OS::Neutron::Net
^^^^^^^^^^^^^^^^^^^^^^^^
::

    [resource_plugin:os_neutron_net]
    enabled = true

Plugin: OS::Neutron::Port
^^^^^^^^^^^^^^^^^^^^^^^^^
::

    [resource_plugin:os_neutron_port]
    enabled = true

Plugin: OS::Neutron::Subnet
^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    [resource_plugin:os_neutron_subnet]
    enabled = true

Plugin: OS::Neutron::Router
^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    [resource_plugin:os_neutron_router]
    enabled = true

Neutron Configuration
=====================

Neutron sends notifications on create/update/delete actions on the
concepts that it implements. Currently Searchlight supports indexing
for networks, subnets, ports and routers.

neutron.conf
------------

Notifications must be configured properly for searchlight to process
incremental updates. Use the following::

    notification_driver = messaging
    notification_topics = searchlight_indexer

.. note::

    Restart the Neutron api service (q-svc) after making changes.

local.conf (devstack)
---------------------

The settings above may be automatically configured by ``stack.sh``
by adding them to the following post config section in devstack.
Just place the following in local.conf and copy the above settings
underneath it.::

  [[post-config|$NEUTRON_CONF]]
  [DEFAULT]

Neutron RBAC Reference
======================

RBAC Filters
------------
RBAC in searchlight neutron plugin is implemented as::

Networks are visible within a tenant OR if they are shared OR if they are external.
Subnets are visible within a tenant OR if their network is shared (OR for admins if their network is external)
Ports are visible within a tenant (OR for admins if their network is shared or external)
Routers are visible within a tenant

Release Notes
=============

0.2.0.0 (Mitaka)
-----------------

DHCP ports are *not* indexed. Neutron doesn't provide a reliable way for
Searchlight to index these ports since they are created and modified
asynchronously from the subnets that they're attached to.

All provider:* properties of networks are exposed to administrators only.
All binding:* properties of ports are also visible only to administrators.
The 'distributed' and 'ha' router properties are available only to
administrators.

Additional properties can be protected similarly with the `admin_only_fields`
under each plugin's configuration section. Glob-like patterns are supported.
For instance::

    [resource_plugin:os_neutron_net]
    admin_only_fields=admin_state_up,status

See: ADMIN_ONLY_FIELDS in:
* searchlight/elasticsearch/plugins/neutron/networks.py
* searchlight/elasticsearch/plugins/neutron/ports.py
* searchlight/elasticsearch/plugins/neutron/routers.py
