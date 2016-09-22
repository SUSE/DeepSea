
prep fio:
  salt.state:
    - tgt: "I@roles:cephfs-client and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmark.cephfs

run fio:
  salt.runner:
    - name: benchmark.run

cleanup fio:
  salt.state:
    - tgt: "I@roles:cephfs-client and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmark.cephfs.cleanup
