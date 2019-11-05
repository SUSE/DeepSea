{% set master = salt['master.minion']() %}

{% if salt['saltutil.runner']('disengage.check', cluster='ceph') == False %}
safety is engaged:
  salt.state:
    - tgt: {{ master }}
    - name: "Run 'salt-run disengage.safety' to disable"
    - failhard: True

{% endif %}

terminate ceph osds:
  salt.runner:
    - name: osd.remove
    - arg: ['I@roles:storage']
    - force: True

reset master configuration:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.reset

rescind roles:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.rescind
