===
ntp
===

Formulas to set up and configure the ntp client or server.

.. note::

    See the full `Salt Formulas installation and usage instructions
    <http://docs.saltstack.com/topics/development/conventions/formulas.html>`_.

Available states
================

.. contents::
    :local:

``ntp``
-------

Installs the ntp package, and optionally, a basic config.

``ntp.server``
--------------

Installs the ntp server, an optional server config, and starts the ntp server.

``ntp.local_server``
--------------------

This forumula uses pillar data to determine if the server is an internal NTP
server or a local server that syncs to the internal NTP server and will write
the ntp.conf file accordingly.

Requires CentOS 5.X or CentOS 6.X.

``ntp.ng``
----------

This state is a re-implementation of the original NTP formula. As a state, ``ntp.ng`` controls both the client and server through pillar parameters. This formula does not require that a configuration file be served directly and instead fully exposes all ntp configuration parameters as set in the pillar.

**Note:** ``ntp.ng`` relies upon some conventions first available in the *Helium* release.
