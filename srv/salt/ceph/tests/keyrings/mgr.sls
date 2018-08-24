
{% set keyring = salt['cmd.shell']("ls /srv/salt/ceph/mgr/cache/*.keyring | head -1") %}
{% set name = "mgr." + salt['cmd.shell']("basename -s .keyring " + keyring) %}

mgr keyring:
  cmd.run:
    - name: "ceph --keyring={{ keyring }} --name={{ name }} fsid >/dev/null"

