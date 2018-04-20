# This benchmark runs fio against a local block device on the given
# node. This can be used for both iSCSI initiator and krbd client
# benchmarks, assuming the iSCSI login or rbd map is performed manually
# beforehand.
# TODO Support per-client block devices
{% set master = salt['master.minion']() %}

prep master:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.benchmarks.blockdev.prepare_master

prep clients:
  salt.state:
    - tgt: "I@roles:benchmark-blockdev and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmarks.blockdev.prepare_clients

run fio:
  salt.runner:
    - name: benchmark.blockdev
    - log_dir: {{ salt['pillar.get']('benchmark:log-file-directory') }}
    - job_dir: {{ salt['pillar.get']('benchmark:job-file-directory') }}
    - default_collection: {{ salt['pillar.get']('benchmark:default-collection') }}
    - client_glob : "I@roles:benchmark-blockdev and I@cluster:ceph"
    # work_dir not used by blockdev bench, as it's not mounted

cleanup clients:
  salt.state:
    - tgt: "I@roles:benchmark-blockdev and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmarks.blockdev.cleanup_clients

# no cleanup for master needed
