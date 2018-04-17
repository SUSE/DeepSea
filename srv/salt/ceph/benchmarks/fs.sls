
{% set master = salt['master.minion']() %}

prep master:
  salt.state:
    - tgt: {{ master }}
    - sls:
      - ceph.benchmarks.fs.prepare_master

prep clients:
  salt.state:
    - tgt: "I@roles:benchmark-fs and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmarks.fs.prepare_clients

run fio:
  salt.runner:
    - name: benchmark.fs
    - work_dir: {{ salt['pillar.get']('benchmark:work-directory') }}
    - log_dir: {{ salt['pillar.get']('benchmark:log-file-directory') }}
    - job_dir: {{ salt['pillar.get']('benchmark:job-file-directory') }}
    - default_collection: {{ salt['pillar.get']('benchmark:default-collection') }}
    - client_glob : "I@roles:benchmark-fs and I@cluster:ceph"

cleanup fio:
  salt.state:
    - tgt: "I@roles:benchmark-fs and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmarks.fs.cleanup
