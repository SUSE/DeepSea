
admin keyring:
  cmd.run:
    - name: "ceph --keyring=/srv/salt/ceph/admin/cache/ceph.client.admin.keyring fsid >/dev/null"
