
prep clients:
  salt.state:
    - tgt: "I@roles:mds-client and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmark.cephfs

one subdir:
  salt.state:
    - tgt: {{  salt.saltutil.runner('select.one_minion', cluster='ceph', roles='mds-client') }}
    - sls:
      -ceph.benchmark.cephfs.working_subdir

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

clean subdir:
  salt.state:
    - tgt: {{  salt.saltutil.runner('select.one_minion', cluster='ceph', roles='mds-client') }}
    - sls:
      -ceph.benchmark.cephfs.cleanup_working_subdir

cleanup fio:
  salt.state:
    - tgt: "I@roles:mds-client and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmark.cephfs.cleanup
