
ganesha apply:
  salt.state:
    - tgt: "I@roles:ganesha and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.ganesha
  