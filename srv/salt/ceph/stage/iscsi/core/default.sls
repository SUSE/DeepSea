
{% set master = salt['master.minion']() %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}

add_mine_cephimages.list_function:
  salt.function:
    - name: mine.send
    - arg:
      - cephimages.list
    - tgt: {{ master }}
    - tgt_type: compound

rbd pool:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.igw.rbd

igw config:
  salt.state:
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.igw.config

auth:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.igw.auth

keyring:
  salt.state:
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.igw.keyring

iscsi apply:
  salt.state:
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.igw

{% endif %}

