
{% if salt['saltutil.runner']('disengage.check', cluster='ceph') == False %}
safety is engaged:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - name: "Run 'salt-run disengage.safety' to disable"
    - failhard: True

{% endif %}

set noout:
  salt.state:
    - sls: ceph.noout.set
    - tgt: {{ salt['master.minion']() }}
    - tgt_type: compound
    - failhard: True

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha') %}
Shutting down ganesha:
  salt.state:
    - sls: ceph.terminate.ganesha
    - tgt: "I@roles:ganesha and I@cluster:ceph"
    - tgt_type: compound
    - failhard: True
{% endif %}

{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
Shutting down radosgw for {{ role }}:
  salt.state:
    - sls: ceph.terminate.rgw
    - tgt: "I@roles:{{ role }} and I@cluster:ceph"
    - tgt_type: compound
    - failhard: True
{% endfor %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') %}
Shutting down cephfs:
  salt.state:
    - sls: ceph.terminate.mds
    - tgt: "I@roles:mds and I@cluster:ceph"
    - tgt_type: compound
    - failhard: True
{% endif %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}
Shutting down iscsi:
  salt.state:
    - sls: ceph.terminate.igw
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
    - failhard: True
{% endif %}

Shutting down storage:
  salt.state:
    - sls: ceph.terminate.storage
    - tgt: "I@roles:storage and I@cluster:ceph"
    - tgt_type: compound
    - failhard: True

Shutting down mgr:
  salt.state:
    - sls: ceph.terminate.mgr
    - tgt: "I@roles:mgr and I@cluster:ceph"
    - tgt_type: compound
    - failhard: True

Shutting down mon:
  salt.state:
    - sls: ceph.terminate.mon
    - tgt: "I@roles:mon and I@cluster:ceph"
    - tgt_type: compound


