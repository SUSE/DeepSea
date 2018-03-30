
{% set keyring = "/srv/salt/ceph/mon/cache/mon.keyring" %}
{% set name = "mon." %}

mon keyring:
  cmd.run:
    - name: "ceph --keyring={{ keyring }} --name={{ name }} fsid >/dev/null"

