
{% set master = salt['master.minion']() %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha') or salt.saltutil.runner('select.minions', cluster='ceph', ganesha_configurations='*') %}

ganesha auth:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.ganesha.auth
    - failhard: True

ganesha config:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.ganesha.config
    - failhard: True

ganesha rados config:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.ganesha.rados_config
    - failhard: True

{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}
start {{ role }}::
  salt.state:
    - tgt: "I@roles:{{ role }} and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.ganesha
    - failhard: True

{% endfor %}

configure dashboard cephfs permissions:
  salt.function:
    - name: cmd.run
    - tgt: {{ master }}
    - tgt_type: compound
    - arg:
      - "ceph config set mgr client_mount_uid 0 && ceph config set mgr client_mount_gid 0"

{% set nfs_pool = salt['master.find_pool'](['cephfs', 'rgw']) %}
configure dashboard nfs:
  salt.function:
    - name: cmd.run
    - tgt: {{ master }}
    - tgt_type: compound
    - arg:
      - "ceph dashboard set-ganesha-clusters-rados-pool-namespace {{ nfs_pool }}/ganesha"

{% endif %}
