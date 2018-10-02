

Starting mon:
  salt.state:
    - sls: ceph.start.mon
    - tgt: "I@roles:mon and I@cluster:ceph"
    - tgt_type: compound

Starting mgr:
  salt.state:
    - sls: ceph.start.mgr
    - tgt: "I@roles:mgr and I@cluster:ceph"
    - tgt_type: compound

Starting storage:
  salt.state:
    - sls: ceph.start.storage
    - tgt: "I@roles:storage and I@cluster:ceph"
    - tgt_type: compound

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}
Starting iscsi:
  salt.state:
    - sls: ceph.start.igw
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
{% endif %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') %}
Starting cephfs:
  salt.state:
    - sls: ceph.start.mds
    - tgt: "I@roles:mds and I@cluster:ceph"
    - tgt_type: compound
{% endif %}

{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
Starting radosgw for {{ role }}:
  salt.state:
    - sls: ceph.start.rgw
    - tgt: "I@roles:{{ role }} and I@cluster:ceph"
    - tgt_type: compound
{% endfor %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha') %}
Starting ganesha:
  salt.state:
    - sls: ceph.start.ganesha
    - tgt: "I@roles:ganesha and I@cluster:ceph"
    - tgt_type: compound
{% endif %}

