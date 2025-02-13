..
    c) Copyright 2015 Hewlett-Packard Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

=================================
 Enabling Searchlight in Devstack
=================================

1. Download DevStack (git clone)

2. Update local.conf

You may follow the customization instructions below or use the example
local.conf.

3. Run ``stack.sh``

.. note::
   This installs a headless JRE. If you are working on a desktop based OS
   (such as Ubuntu 14.04), this may cause tools like pycharms to no longer
   launch. You can switch between JREs and back: to a headed JRE version using:
   "sudo update-alternatives --config java".


Full example local.conf
=======================

The example local.conf MAY not be up to date with the rest of devstack.

:download:`local.conf <local.conf>`

.. note::
   You will need to look through the settings and potentially customize it to your
   environment, especially ``HOST_IP``.

Existing local.conf customization
=================================

1. Add this repo as an external repository::

     > cat local.conf
     [[local|localrc]]
     enable_plugin searchlight https://github.com/openstack/searchlight
     enable_service searchlight-api
     enable_service searchlight-listener

2. Configure desired searchlight plugins

The search service is driven using a plugin mechanism for integrating to other
services. Each integrated service may need to be specifically enabled
in devstack and may require additional configuration settings to work with
searchlight. For example, typically, you will need to add the
``searchlight_indexer`` notification topic to each service's configuration.

Please review the plugin documentation and add configuration appropriately:

 * `Searchlight Plugins <http://docs.openstack.org/developer/searchlight/plugins.html>`_

3. Customize searchlight configuration

Searchlight documentation talks about settings in ``searchlight.conf``.
To customize searchlight.conf settingss, add then under the following
section in ``local.conf``::

    [[post-config|$SEARCHLIGHT_CONF]]
