

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') %}

{% set keyring = salt['cmd.shell']("ls /srv/salt/ceph/mds/cache/*.keyring | head -1") %}
{% set name = "mds." + salt['cmd.shell']("basename -s .keyring " + keyring) %}

mds keyring:
  cmd.run:
    - name: "ceph --keyring={{ keyring }} --name={{ name }} fsid >/dev/null"

restricted mds keyring:
  cmd.run:
    - name: "ceph --keyring={{ keyring }} --name={{ name }} auth list >/dev/null; [ $? != 0 ]"

{% else %}

skipping mds:
  test.nop

{% endif %}
