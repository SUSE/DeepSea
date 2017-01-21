
prep master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls:
      - ceph.cephfs.benchmarks.prepare_master

prep clients:
  salt.state:
    - tgt: "I@roles:client-cephfs and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.cephfs.benchmarks.prepare_clients

one subdir:
  salt.state:
    - tgt: {{  salt.saltutil.runner('select.one_minion', cluster='ceph', roles='client-cephfs') }}
    - sls:
      - ceph.cephfs.benchmarks.working_subdir

run fio:
  salt.runner:
    - name: benchmark.cephfs
    - work_dir: {{ salt['pillar.get']('benchmark:work-directory') }}
    - log_dir: {{ salt['pillar.get']('benchmark:log-file-directory') }}
    - job_dir: {{ salt['pillar.get']('benchmark:job-file-directory') }}
    - default_collection: {{ salt['pillar.get']('benchmark:default-collection') }}
    - client_glob : "I@roles:client-cephfs and I@cluster:ceph"

clean subdir:
  salt.state:
    - tgt: {{  salt.saltutil.runner('select.one_minion', cluster='ceph', roles='client-cephfs') }}
    - sls:
      - ceph.cephfs.benchmarks.cleanup_working_subdir

cleanup fio:
  salt.state:
    - tgt: "I@roles:client-cephfs and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.cephfs.benchmarks.cleanup

remove auth key:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.cephfs.benchmarks.cleanup_key_auth
