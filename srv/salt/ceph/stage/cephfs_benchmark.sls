
prep fio:
  salt.state:
    - tgt: "I@roles:mds-client and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmark.cephfs

run fio:
  salt.runner:
    - name: benchmark.run
    - work_dir: {{ salt['pillar.get']('benchmark:work-directory') }}
    - default_collection: {{ salt['pillar.get']('benchmark:default-collection') }}

cleanup fio:
  salt.state:
    - tgt: "I@roles:mds-client and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmark.cephfs.cleanup
