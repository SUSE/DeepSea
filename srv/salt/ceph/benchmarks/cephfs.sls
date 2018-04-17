
{% set master = salt['master.minion']() %}

prep master:
  salt.state:
    - tgt: {{ master }}
    - sls:
      - ceph.cephfs.benchmarks.prepare_master

prep clients:
  salt.state:
    - tgt: "I@roles:client-cephfs and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.cephfs.benchmarks.prepare_clients
    - pillar:
        'mount_mon_hosts': {{ salt.saltutil.runner('select.public_addresses', cluster='ceph', roles='mon') | join(',') }}
        'mount_opts': -o name=deepsea_cephfs_bench,secretfile=/etc/ceph/ceph.client.deepsea_cephfs_bench.secret,{{ salt['pillar.get']('benchmark:extra_mount_opts') }}

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
    - tgt: {{ master }}
    - sls: ceph.cephfs.benchmarks.cleanup_key_auth
