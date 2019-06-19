{% set master = salt['pillar.get']('master_minion) %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') %}

{% if salt['saltutil.runner']('validate.discovery', cluster='ceph') == False %}

validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ master }}
    - failhard: True

{% endif %}

refresh_pillar1:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.refresh

create renamed mds keys:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.mds.key
    - failhard: True

push mds keys:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.mds.key
    - failhard: True

auth new keys:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.mds.auth
    - failhard: True

deploy renamed mds:
  salt.state:
    - tgt: "I@roles:mds and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.mds
    - failhard: True

remove old mds:
  salt.state:
    - tgt: "I@roles:mds and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.mds.remove-mds-with-numeric-names

{% endif %}

