Ceph is highly dependent on accurate time, meaning time sync across the server is critical to Ceph. If we further consider that a large number of ceph deployments are in air-gapped network environments and won't have access to standard time servers, it becomes necessary to sync with time servers that exist within the air-gapped environment. One of the prime design tents of Deepsea is to produce a minimal useful cluster out of the box; the product of all of this, for a user who hasn't had the foresight or technical skill to set up a time server in the air-gapped environment, it is appropriate for DeepSea to be able to configure a basic time server and to distribute the configuration to the nodes.

In order to facilitate this goal and to fight against "feature creep," DeepSea should adhere to the below requirements for the time service. These requirements are considered the maximum reasonable feature set for DeepSea. If the user has requirements that are more advanced than can be accommodated by this specification, they will need to disable DeepSea's NTP management and configure their own.

Requirements
------------
- DeepSea should be able to configure each node as a time sync client.
- DeepSea should be able to configure one node as a time sync server which all other clients will reference.
- DeepSea should manage cluster time synchronization by default.
- The user should be able to configure basic time sync options via a central configuration file.
- The user should be able to disable time synchronization management by deletion of the relevant section in the config file.
- The user should be able to specify which node, if any, is to be configured as the time server. In the absence of a specification, all nodes should be configured as clients.
- The user should be able to specify which external server(s), if any, are to be used as a higher-level, master reference. (NTP would call these 'higher stratum servers'.)
  - If DeepSea is managing a time server, the server should be configured to reference these 'master servers', and all clients should be configured to reference the DeepSea-managed time server.
  - If DeepSea is not managing a time server, all clients should be configured to reference these 'master servers' instead of a DeepSea-managed time server.
  - I this section is deleted, reasonable default values should be assumed.
  - If the time server cannot reach these 'master servers' to get its own time reference, it should use its own system clock as a time reference.
- Based on user requests, the user should be able to provide his/her own custom configuration files to be distributed to the cluster.
  - Server and client variants of custom files should be supported, with server variants distributed only to the time sync server (if specified) and client variants distributed to all non-server nodes.

Implementation
--------------
NTP will be used to meet the above requirements for both server and client management for two main reasons. Firstly, NTP is a ubiquitous, stable, time-tested technology. Secondly, SaltStack provides an NTP formula (https://github.com/saltstack-formulas/ntp-formula) which can be leveraged to reduce initial and ongoing development efforts to support this feature. The configuration file (more below) will be designed with specific reference to NTP and using NTP terminology to increase transparency to the user.

Configuration
-------------

The configuration file will obey the following parameters. The below parameters are the default values configured upon a fresh configuration.

__`srv/pillar/ceph/stack/global.yml`__
```yml
time_service:
  manage: true
  ntp_server: {{ pillar.get('master_minion') }}
  higher_stratum_servers:
    - '0.pool.ntp.org'
    - '1.pool.ntp.org'
    - '2.pool.ntp.org'
    - '3.pool.ntp.org'
  ntp_server_conf: ntp-server-default.conf
  ntp_client_conf: ntp-client-default.conf
```

### `time_service`
This is the YAML section header for configuring DeepSea's time service management. If this section is removed entirely, DeepSea will not manage a time service (provide backwards compatibility with older config files).

#### `manage`
This setting provides an explicit means of enabling/disabling DeepSea's time service management. If this value is set to `true` (default), DeepSea will manage a time service. If this value is set to `false` or the key is removed entirely, DeepSea will not manage a time service.

#### `ntp_server`
This setting determines which server (if any) to configure as an NTP server. By default, this value is set such that DeepSea will configure the DeepSea (Salt) master as an NTP server. This value may be changed to the Salt minion ID of any single node managed by DeepSea, which DeepSea will configure as the NTP server instead. If the key is removed entirely, DeepSea will not configure any node as an NTP server.

#### `higher_stratum_servers`
This setting determines which higher stratum servers to use as master time servers for the cluster. By default, this value is set to the first 4 NTP servers from `pool.ntp.org`. If this section is deleted, these 4 NTP servers will be used as reasonable defaults. The user may specify, in YAML list format, as many (or as few as one) NTP servers as they wish. This setting has two basic modes of operation:

__DeepSea is managing an NTP server as configured by `ntp_server`__

In this mode, the NTP server will reference the servers defined by `higher_stratum_servers`, and all other DeepSea nodes will reference the NTP server. The server will reference its own system clock if these servers are not reachable.

__DeepSea is not managing an NTP server as configured by `ntp_server`__

In this mode, all nodes will be configured to reference the servers defined by `higher_stratum_servers`. The nodes will __not__ reference their own system clocks if these servers are not reachable.

#### `ntp_server_conf` and `ntp_client_conf`
These settings define the source files DeepSea will use to distribute `ntp.conf` files on the NTP server and clients. These values are where a user may specify custom NTP configuration files to be distributed instead of DeepSea's basic versions. The `ntp_server_conf` file will be distributed only to the NTP server and only a server it is specified by `ntp_server`. The `ntp_client_conf` file will be distributed to all nodes not specified by `ntp_server`. NTP config files must be placed in '/srv/formulas/deepsea-ntp-formula/ntp/'. A few important notes and clarifications:
- If these two settings are removed entirely, the default files `ntp-server-default.conf` and `ntp-client-default.conf` will be used.
- These files, whether server or client, will always be named `ntp.conf` on a node onto which DeepSea deploys them.
- Custom files will not obey the `higher_stratum_servers` setting to prevent unwanted interference with them. The default files configured by DeepSea, 'ntp-server-default.conf' and 'ntp-client-default.conf', do obey the 'higher_stratum_servers' setting.

Migrating from a DeepSea-managed time service to a user-managed time service
----------------------------------------------------------------------------
If the user wishes to no longer use DeepSea to manage their cluster time service, they should disable time service management as defined above via the configuration file. If NTP will not be used, uninstalling the NTP package from the systems manually will be necessary. After this, it is safe to migrate to another system for managing the cluster time service. 

Migrating from a user-managed time service to a DeepSea-managed time service
----------------------------------------------------------------------------
If the user wishes to use DeepSea to manage their time service after previously using a custom service or configuration, it is safest to ensure the previous configuration is removed completely, not merely disabled. After the user is sure the previous service is no longer managing the cluster time service, they should enable the DeepSea time service management as defined above via the configuration file. After this, run all DeepSea stages, checking for errors along the way, to ensure the configuration works as expected.