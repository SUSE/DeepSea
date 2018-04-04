
{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw')  %}

{% set keyring = salt['cmd.shell']("ls /srv/salt/ceph/rgw/cache/*.keyring | head -1") %}
{% set name = salt['cmd.shell']("basename -s .keyring " + keyring) %}

rgw keyring:
  cmd.run:
    - name: "ceph --keyring={{ keyring }} --name={{ name }} fsid >/dev/null"

{% else %}

skipping rgw:
  test.nop

{% endif %}
