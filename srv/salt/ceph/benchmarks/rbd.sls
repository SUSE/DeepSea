
{% set master = salt['master.minion']() %}

prep master:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.rbd.benchmarks.prepare_master

prep clients:
  salt.state:
    - tgt: "I@roles:benchmark-rbd and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.rbd.benchmarks.prepare_clients

# run rbd benchmark runner
run fio:
  salt.runner:
    - name: benchmark.rbd
    - work_dir: {{ salt['pillar.get']('benchmark:work-directory') }}
    - log_dir: {{ salt['pillar.get']('benchmark:log-file-directory') }}
    - job_dir: {{ salt['pillar.get']('benchmark:job-file-directory') }}
    - default_collection: {{ salt['pillar.get']('benchmark:default-collection') }}
    - client_glob : "I@roles:benchmark-rbd and I@cluster:ceph"

cleanup clients:
  salt.state:
    - tgt: "I@roles:benchmark-rbd and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.rbd.benchmarks.cleanup_clients

cleanup master:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.rbd.benchmarks.cleanup_master

