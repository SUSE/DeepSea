
{% set keyring = "/srv/salt/ceph/osd/cache/ceph.client.storage.keyring" %}
{% set name = "client.storage" %}

storage keyring:
  cmd.run:
    - name: "ceph --keyring={{ keyring }} --name={{ name }} fsid >/dev/null"

restricted storage keyring:
  cmd.run:
    - name: "ceph --keyring={{ keyring }} --name={{ name }} auth list >/dev/null; [ $? != 0 ]"


