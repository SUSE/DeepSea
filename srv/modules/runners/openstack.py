# -*- coding: utf-8 -*-
# vim: ts=8 et sw=4 sts=4
"""
Wrapper to apply the ceph.openstack state to the salt master, then
return the ceph configuration and keys necessary to subsequently
configure OpenStack.
"""

from __future__ import absolute_import
import re
import salt.client

try:
    import configparser
except ImportError:
    import salt.ext.six.moves.configparser as configparser
from cStringIO import StringIO


def integrate(**kwargs):
    """
    Create pools and users necessary for OpenStack integration.  Returns
    relevant Ceph configuration and keys, to be used to subsequently
    configure OpenStack.

    This will create pools for use by glance, cinder, cinder-backup and nova.
    By default, these pools will be named "cloud-images", "cloud-volumes",
    "cloud-backups" and "cloud-vms" respectively.  If these names conflict
    with any existing pools, or if you wish to have a single Ceph cluster
    provide storage for multiple OpenStack deployments, use of the "prefix"
    parameter will alter the pool names, for example specifying "prefix=other"
    will result in pools named "other-cloud-images", "other-cloud-volumes",
    "other-cloud-backups" and "other-cloud-vms".

    Similarly, by default, this function will create users named
    "client.glance", "client.cinder" and "client.cinder-backup".  Specifying
    "prefix=other" would result in users named "client.other-glance",
    "client.other-cinder" and "client.other-cinder-backup" (there is no
    separate nova user; nova should be configured to access the cluster using
    the cinder key).

    CLI Example:

        salt-run --out=yaml openstack.integrate
        salt-run --out=yaml openstack.integrate prefix=other

    Sample Output:

        ceph_conf:
          cluster_network: 172.16.2.0/24
          fsid: 049c4577-3806-3e5b-944e-eec8bedb12bc
          mon_host: 172.16.1.13, 172.16.1.12, 172.16.1.11
          mon_initial_members: mon3, mon2, mon1
          public_network: 172.16.1.0/24
        cinder:
          key: AQAcJiJbAAAAABAAsJs2RbFr0bhDRP43Lj3h/g==
          rbd_store_pool: cloud-volumes
          rbd_store_user: cinder
        cinder-backup:
          key: AQAcJiJbAAAAABAAdbLzrL5QoXoqv+FzGQKg5Q==
          rbd_store_pool: cloud-backups
          rbd_store_user: cinder-backup
        glance:
          key: AQAcJiJbAAAAABAA8LLSGbhzblBK96WNDWzNiQ==
          rbd_store_pool: cloud-images
          rbd_store_user: glance
        nova:
          rbd_store_pool: cloud-vms
        radosgw_urls:
        - https://data4.ceph:443/swift/v1

    The ceph_conf information returned is the minimum data required to
    construct a suitable /etc/ceph/ceph.conf file on the OpenStack hosts.
    The cinder, cinder-backup and glance sections include the keys
    that need to be written to the appropriate ceph.client.*.keyring files
    in /etc/ceph/.  The various rbd_store_pool and rbd_store_user settings
    are for use in the cinder, cinder-backup, glance and nova configuration
    files.  The radosgw_urls list will be populated auomatically, based on
    whatever RGW instances have been configured.  If RGW has not been
    configured (or if this runner can't figure out what the URL is based on
    what's in ceph.conf), this will be an empty list.  If there are multiple
    RGW instances, they will all be included in the list, and it's up to the
    administrator to choose the correct one when configuring OpenStack.

    Note that to correctly configure RGW for use by OpenStack, the following
    must be set in /srv/salt/ceph/configuration/files/ceph.conf.d/rgw.conf:

        rgw keystone api version = 3
        rgw keystone url = http://192.168.126.2:5000/
        rgw keystone admin user = ceph
        rgw keystone admin password = verybadpassword
        rgw keystone admin domain = Default
        rgw keystone admin project = admin
        rgw keystone verify ssl = false

    The user, password, project and domain need to match what has been
    configured on the OpenStack side.  Note that these settings tend to be
    case-sensitive, i.e. "Default" and "default" are not the same thing.
    Also, real-world deployments are expected to use SSL, and choose a
    better password than is specified above.
    """
    local = salt.client.LocalClient()

    master_minion = local.cmd('I@roles:master', 'pillar.get',
                              ['master_minion'],
                              expr_form='compound').items()[0][1]

    prefix = ""
    if "prefix" in kwargs:
        state_res = local.cmd(master_minion, 'state.apply', ['ceph.openstack',
                              'pillar={"openstack_prefix": "' + kwargs['prefix'] + '"}'])
        # Set up prefix for subsequent string concatenation to match what's done
        # in the SLS files for keyring and pool names.
        prefix = "{}-".format(kwargs['prefix'])
    else:
        state_res = local.cmd(master_minion, 'state.apply', ['ceph.openstack'])

    # If state.apply failed for any reason, this will return whatever
    # state(s) failed to apply
    failed = []
    for _, states in state_res.items():
        if isinstance(states, dict):
            for _, state in states.items():
                if 'result' not in state or not state['result']:
                    failed.append(state)
        else:
            # This could happen if the SLS being applied somehow doesn't exist,
            # e.g. "No matching sls found for 'ceph.openstack' in env 'base'".
            # Realistically this should never /actually/ happen.
            failed.append(states)
    if failed:
        return {'ERROR': failed}

    runner = salt.runner.RunnerClient(__opts__)

    def _local(*args):
        """
        salt.client.LocalClient.cmd() returns a dict keyed by minion ID.  For
        cases where we're running a single command on the master and want the
        result, this is a convenient shorthand.
        """
        # pylint: disable=no-value-for-parameter
        return list(local.cmd(master_minion, *args).items())[0][1]

    fsid = _local('pillar.get', ['fsid'])
    public_network = _local('pillar.get', ['public_network'])
    cluster_network = _local('pillar.get', ['cluster_network'])
    mon_initial_members = ", ".join(runner.cmd('select.minions',
                                               ['cluster=ceph', 'roles=mon', 'host=True'],
                                               print_event=False))
    mon_host = ", ".join(runner.cmd('select.public_addresses',
                                    ['cluster=ceph', 'roles=mon'], print_event=False))

    cinder_key = _local('keyring.secret', [_local('keyring.file', ['cinder', prefix])])
    backup_key = _local('keyring.secret', [_local('keyring.file', ['cinder-backup', prefix])])
    glance_key = _local('keyring.secret', [_local('keyring.file', ['glance', prefix])])

    conf = configparser.RawConfigParser()
    with open("/srv/salt/ceph/configuration/cache/ceph.conf") as lines:
        conf.readfp(StringIO('\n'.join(line.strip() for line in lines)))

    rgw_urls = []
    rgw_configurations = runner.cmd('select.from',
                                    ['pillar=rgw_configurations', 'role=rgw', 'attr=host'],
                                    print_event=False)
    for rgw in rgw_configurations:
        section = "client.{}.{}".format(rgw[0], rgw[1])
        if not conf.has_section(section):
            continue
        if conf.has_option(section, "rgw frontends") and conf.has_option(section, "rgw dns name"):
            https = re.match(r'.*port=(\d+)s.*', conf.get(section, "rgw frontends"))
            http = re.match(r'.*port=(\d+).*', conf.get(section, "rgw frontends"))
            if not http and not https:
                continue
            if http:
                url = "http://{}:{}/swift/v1".format(conf.get(section, "rgw dns name"),
                                                     http.group(1))
            if https:
                url = "https://{}:{}/swift/v1".format(conf.get(section, "rgw dns name"),
                                                      https.group(1))
            rgw_urls.append(url)

    return {
        'ceph_conf': {
            'fsid': fsid,
            'mon_initial_members': mon_initial_members,
            'mon_host': mon_host,
            'public_network': public_network,
            'cluster_network': cluster_network
        },
        'cinder': {
            'rbd_store_pool': prefix + 'cloud-volumes',
            'rbd_store_user': prefix + 'cinder',
            'key': cinder_key
        },
        'cinder-backup': {
            'rbd_store_pool': prefix + 'cloud-backups',
            'rbd_store_user': prefix + 'cinder-backup',
            'key': backup_key
        },
        'glance': {
            'rbd_store_pool': prefix + 'cloud-images',
            'rbd_store_user': prefix + 'glance',
            'key': glance_key
        },
        'nova': {
            'rbd_store_pool': prefix + 'cloud-vms'
        },
        'radosgw_urls': rgw_urls
    }
