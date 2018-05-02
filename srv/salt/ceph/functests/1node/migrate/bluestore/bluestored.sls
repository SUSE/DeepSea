
{% set node = salt.saltutil.runner('select.first', roles='storage') %}
{% set label = "btobd" %}

Remove OSDs {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.tests.migrate.remove_osds
       
Remove destroyed {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.remove.destroyed

Initialize OSDs {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.tests.migrate.init_osds
    - pillar: {{ salt.saltutil.runner('smoketests.pillar', minion=node, configuration='bluestore') }}
       
Save reset checklist {{ label }}:
  salt.runner:
    - name: smoketests.checklist
    - arg:
        - {{ node }}
        - 'bluestore'

Check reset OSDs {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.tests.migrate.check_osds
    - pillar: {{ salt.saltutil.runner('smoketests.pillar', minion=node, configuration='bluestore') }}
    - failhard: True

Migrate {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.redeploy.osds
    - pillar: {{ salt.saltutil.runner('smoketests.pillar', minion=node, configuration='bluestored') }}

Save checklist {{ label }}:
  salt.runner:
    - name: smoketests.checklist
    - arg:
        - {{ node }}
        - 'bluestored'

Check OSDs {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.tests.migrate.check_osds
    - pillar: {{ salt.saltutil.runner('smoketests.pillar', minion=node, configuration='bluestored') }}


