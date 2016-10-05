
prep clients:
  salt.state:
    - tgt: "I@roles:mds-client and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmark.cephfs

prep master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls:
      - ceph.benchmark.cephfs.prepare_master

run fio:
  salt.runner:
    - name: benchmark.run
    - work_dir: {{ salt['pillar.get']('benchmark:work-directory') }}
    - log_dir: {{ salt['pillar.get']('benchmark:log-file-directory') }}
    - default_collection: {{ salt['pillar.get']('benchmark:default-collection') }}

cleanup fio:
  salt.state:
    - tgt: "I@roles:mds-client and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmark.cephfs.cleanup
