
cephfs data:
  cmd.run:
    - name: "ceph osd pool create cephfs_data 256"
    - unless: "rados lspools | grep -q cephfs_data"

cephfs metadata:
  cmd.run:
    - name: "ceph osd pool create cephfs_metadata 256"
    - unless: "rados lspools | grep -q cephfs_metadata"

cephfs:
  cmd.run:
    - name: "ceph fs new cephfs cephfs_metadata cephfs_data"
    - unless: "ceph fs ls | grep -q ^name"

