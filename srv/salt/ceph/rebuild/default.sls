
{% set master = salt['pillar.get']('master_minion') %}

{% if salt['saltutil.runner']('disengage.check', cluster='ceph') == False %}
safety is engaged:
  salt.state:
    - tgt: {{ master }}
    - name: "Run 'salt-run disengage.safety' to disable"
    - failhard: True

{% endif %}

wait on healthy cluster:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.wait.until.OK
    - failhard: True

{% if salt['saltutil.runner']('filequeue.empty', queue='rebuild') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage') %}
queue {{ host }}:
  salt.runner:
    - name: filequeue.add
    - queue: 'rebuild'
    - item: {{ host }}

{% endfor %}

advise rebuild:
  salt.runner:
    - name: advise.rebuild

{% endif %}

{% for host in salt['saltutil.runner']('filequeue.array', queue='rebuild') %}
lock obliterate {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.obliterate.lock

remove osds {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.obliterate
    - failhard: True
    - require: 
      - salt: lock obliterate {{ host }}

create osds {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.osd
    - failhard: True

update grains {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.osd.grains
    - failhard: True

wait on healthy cluster {{ host }}:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.wait.1hour.until.OK
    - failhard: True

queue {{ host }}:
  salt.runner:
    - name: filequeue.remove
    - queue: 'rebuild'
    - item: {{ host }}

unlock obliterate {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.obliterate.unlock
    - failhard: True

{% endfor %}

cleanup osds:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.remove.destroyed

