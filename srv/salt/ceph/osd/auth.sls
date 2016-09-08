
include:
  - .keyring

add auth:
  cmd.run:
    - name: "ceph auth add client.bootstrap-osd -i /var/lib/ceph/bootstrap-osd/ceph.keyring"

