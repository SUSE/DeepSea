
ganesha install:
  salt.state:
    - tgt: "I@roles:ganesha and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.ganesha.install

ganesha configure:
  salt.state:
    - tgt: "I@roles:ganesha and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.ganesha.configure

ganesha service:
  salt.state:
    - tgt: "I@roles:ganesha and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.ganesha
