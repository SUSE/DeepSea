# benchmark blockdevices that are to be used for osds

prep master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.benchmarks.osd_blockdev.prepare_master

prep clients:
  salt.state:
    - tgt: "I@roles:storage and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmarks.osd_blockdev.prepare_clients

run fio:
  salt.runner:
    - name: benchmark.osd_blockdev
    - log_dir: {{ salt['pillar.get']('benchmark:log-file-directory') }}
    - job_dir: {{ salt['pillar.get']('benchmark:job-file-directory') }}
    - default_collection: {{ salt['pillar.get']('benchmark:default-collection') }}
    - client_glob : "I@roles:storage and I@cluster:ceph"
    # work_dir not used by blockdev bench, as it's not mounted

cleanup clients:
  salt.state:
    - tgt: "I@roles:storage and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.benchmarks.osd_blockdev.cleanup_clients

# no cleanup for master needed
