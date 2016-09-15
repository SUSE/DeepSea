
fio:
  salt.state:
    - tgt: "I@roles:cephs-client and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmark.cephfs.fio
      - ceph.benchmark.cephfs.mount
