..
      Copyright 2015 Hewlett-Packard Development Company, L.P.
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _searchlight-plugins:

Searchlight Plugin Documentation
================================

The search service determines the types of information that is searchable
via a plugin mechanism.

Installing Plugins
------------------

Plugins must be registered in ``setup.cfg``.

Within ``setup.cfg`` the setting within ``[entry_points]`` named
``searchlight.index_backend`` should list the plugin for each available
indexable type. After making a change, it's necessary to re-install the
python package (for instance with ``pip install -e .``).

Each plugin registered in ``setup.cfg`` is enabled by default. Typically it
should only be necessary to modify ``setup.cfg`` if you are installing a new
plugin. It is not necessary to modify ``[entry_points]`` to temporarily
enable or disable installed plugins. Once they are installed, they can be
disabled, enabled and configured in the ``searchlight.conf`` file.

Configuring Plugins
-------------------

After installation, plugins are configured in ``searchlight.conf``.

.. note::

    After making changes to ``searchlight.conf`` you must perform the
    actions indicated in the tables below.

    1. ``Restart services``: Restart all running ``searchlight-api`` *and*
       ``searchlight-listener`` processes.

    2. ``Re-index affected types``: You will need to re-index any resource
       types affected by the change. (See :doc:`indexingservice`).

.. note::

    Unless you are changing to a non-default value, you do not need to
    specify any of the following configuration options.

.. _end-to-end-plugin-configuration-example:

End to End Configuration Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following shows a sampling of various configuration options in
``searchlight.conf``. These are **NOT** necessarily recommended
or default configuration values. They are intended for exemplary purposes only.
Please read the rest of the guide for detailed information.::

    [resource_plugin]
    resource_group_name = searchlight

    [resource_plugin:os_nova_server]
    enabled = True
    admin_only_fields = OS-EXT-SRV*,OS-EXT-STS:vm_state

    [resource_plugin:os_glance_image]
    enabled = True

    [resource_plugin:os_glance_metadef]
    enabled = True

    [resource_plugin:os_cinder_volume]
    enabled = True

    [resource_plugin:os_cinder_snapshot]
    enabled = True

    [resource_plugin:os_neutron_net]
    enabled = True
    admin_only_fields=admin_state_up,status

    [resource_plugin:os_neutron_port]
    enabled = True

    [resource_plugin:os_designate_zone]
    enabled = False

    [resource_plugin:os_designate_recordset]
    enabled = False

    [resource_plugin:os_swift_account]
    enabled = False

    [resource_plugin:os_swift_container]
    enabled = False

    [resource_plugin:os_swift_object]
    enabled = False

Common Plugin Configuration Options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are common configuration options that all plugins honor. They are split
between *global*, *inheritable* and *non-inheritable* options.

**Global** plugin configuration options apply to all plugins and cannot be
overridden by an individual plugin.

**Inheritable** common configuration options may be specified in a default
configuration group of ``[resource_plugin]`` in ``searchlight.conf`` and
optionally overridden in a specific plugin's configuration. For example::

    [resource_plugin]
    notifications_topic = searchlight_indexer

    [resource_plugin:os_nova_server]
    notifications_topic = searchlight_indexer_nova

**Non-Inheritable** common configuration options are honored by all plugins,
but must be specified directly in that plugin's configuration group. They
are not inherited from the ``[resource_plugin]`` configuration group. For
example::

    [resource_plugin:os_glance_image]
    enabled = false

Notification topics are a special case. It is possible to override
the notification ``topic`` as a shared setting; it is also possible to
override ``<topic>,<exchange>`` pairs per-plugin in the case where some
services are using different topics. For instance, in a setup where (for
example) neutron is using a separate notification topic::

    [resource_plugin]
    notifications_topic = searchlight_indexer

    [resource_plugin:os_nova_server]
    notifications_topics_exchanges = searchlight_indexer,nova
    notifications_topics_exchanges = another-topic,neutron

If you override one service topic, you must provide topic,exchange pairs
for all service notifications a plugin supports.

See :ref:`individual-plugin-configuration` for more information and examples
on individual plugin configuration.

Global Configuration Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------+---------------+-------------------------------------+---------------------------+
| Option              | Default value | Description                         | Action(s) Required        |
+=====================+===============+=====================================+===========================+
| resource_group_name | searchlight   | Determines the ElasticSearch index  |                           |
|                     |               | and alias where documents will be   | | Restart services        |
|                     |               | stored. Index names will be         | Re-index all types        |
|                     |               | suffixed with a timestamp.          |                           |
+---------------------+---------------+-------------------------------------+---------------------------+

Inheritable Common Configuration Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------+---------------+-------------------------------------+---------------------------+
| Option              | Default value | Description                         | Action(s) Required        |
+=====================+===============+=====================================+===========================+
| mapping_use\_       |               | Use doc_values to store documents   |                           |
|    doc_values       | true          | rather than fieldata. doc_values    | | Full re-index           |
|                     |               | has some advantages, particularly   |                           |
|                     |               | around memory usage.                |                           |
+---------------------+---------------+-------------------------------------+---------------------------+
| notifications_topic | searchlight\_ | The oslo.messaging topic on which   | | Restart listener        |
|                     |   indexer     | services send notifications. Each   |                           |
|                     |               | plugin defines a list of exchanges  |                           |
|                     |               | to which it will subscribe.         |                           |
+---------------------+---------------+-------------------------------------+---------------------------+

Non-Inheritable Common Configuration Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------+---------------+-------------------------------------+---------------------------+
| Option              | Default value | Description                         | Action(s) Required        |
+=====================+===============+=====================================+===========================+
| enabled             | true          | An installed plugin may be enabled  | | Restart services        |
|                     |               | (true) or disabled (false). When    | | Re-index affected types |
|                     |               | disabled, it will not be available  |                           |
|                     |               | for bulk indexing, notification     |                           |
|                     |               | listening, or searching.            |                           |
+---------------------+---------------+-------------------------------------+---------------------------+
| admin_only_fields   | <none>        | A comma separated list of fields    | | Restart services        |
|                     |               | (wildcards allowed) that are only   | | Re-index affected types |
|                     |               | visible to administrators, and only |                           |
|                     |               | searchable by administrators. Non-  |                           |
|                     |               | administrative users will not be    |                           |
|                     |               | able to see or search on these      |                           |
|                     |               | fields.                             |                           |
|                     |               | These fields are typically          |                           |
|                     |               | specified for search performance,   |                           |
|                     |               | search accuracy, or security        |                           |
|                     |               | reasons.                            |                           |
|                     |               | or security reasons.                |                           |
|                     |               | If a plugin has a hard-coded        |                           |
|                     |               | mapping for a specific field, it    |                           |
|                     |               | will take precedence over this      |                           |
|                     |               | configuration option.               |                           |
+---------------------+---------------+-------------------------------------+---------------------------+
| notifications\_     | <none>        | Override topic,exchange pairs (see  | | Restart services        |
|  topics_exchanges   |               | note above). Use when services      |                           |
|                     |               | output notifications on dissimilar  |                           |
|                     |               | topics.                             |                           |
+---------------------+---------------+-------------------------------------+---------------------------+

.. _individual-plugin-configuration:

Individual Plugin Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Individual plugins may also be configured in  ``searchlight.conf``.

.. note::

    Plugin configurations are typically named based on their resource type.
    The configuration name uses the following naming pattern:

    * The resource type name changed to all lower case

    * All ``::`` (colons) converted into ``_`` (underscores).

    For example: OS::Glance::Image --> [resource_plugin:os_glance_image]

To override a default configuration option on a specific plugin, you must
specify a configuration group for that plugin with the option(s) that you
want to override. For example, if you wanted to **just** disable the Glance
image plugin, you would add the following configuration group::

    [resource_plugin:os_glance_image]
    enabled = false

Each plugin may have additional configuration options specific to it.
Information about those configuration options will be found in documentation
for that plugin.

Finally, each integrated service (Glance, Nova, etc) may require
additional configuration settings. For example, typically, you will need
to add the ``searchlight_indexer`` notification topic to each service's
configuration in order for Searchlight to receive incremental updates from
that service.

Please review each plugin's documentation for more information:

.. toctree::
   :maxdepth: 1
   :glob:

   plugins/*
