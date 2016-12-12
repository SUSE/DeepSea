create benchmark image:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.rbd.benchmarks.create_image

prep clients:
  salt.state:
    - tgt: "I@roles:client-rbd and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.rbd.benchmarks.prepare_clients

# run rbd benchmark runner

cleanup clients:
  salt.state:
    - tgt: "I@roles:client-rbd and I@cluster:ceph"
    - tgt_type: compound
    - sls:
      - ceph.rbd.benchmarks.cleanup_clients

delete benchmark image:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.rbd.benchmarks.delete_image

