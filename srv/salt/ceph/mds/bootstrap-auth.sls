
include:
  - .keyring

add auth:
  cmd.run:
    - name: "ceph auth add client.bootstrap-mds -i /var/lib/ceph/bootstrap-mds/ceph.keyring"

