prep master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls:
      - ceph.ganesha.benchmarks.prepare_master

{% set ganesha_server = salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha')[0] %}
prep clients:
  salt.state:
    - tgt: "I@roles:client-nfs and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.ganesha.benchmarks.prepare_clients
    - pillar:
        'ganesha-server': {{ salt.saltutil.runner('select.public_addresses', cluster='ceph', roles='ganesha') | join(',') }}

run fio:
  salt.runner:
    - name: benchmark.ganesha
    - work_dir: {{ salt['pillar.get']('benchmark:work-directory') }}
    - log_dir: {{ salt['pillar.get']('benchmark:log-file-directory') }}
    - job_dir: {{ salt['pillar.get']('benchmark:job-file-directory') }}
    - default_collection: {{ salt['pillar.get']('benchmark:default-collection') }}
    - client_glob : "I@roles:client-nfs and I@cluster:ceph"

cleanup fio:
  salt.state:
    - tgt: "I@roles:client-nfs and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.ganesha.benchmarks.cleanup

