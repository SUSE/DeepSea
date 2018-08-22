
{% set node = salt.saltutil.runner('select.first', roles='storage') %}
{% set label = "f2tob" %}

Check environment {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.tests.migrate.check3
    - failhard: True

Remove OSDs {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.tests.migrate.remove_osds
    - failhard: True
       
Remove destroyed {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.remove.destroyed
    - failhard: True

Initialize OSDs {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.tests.migrate.init_osds
    - pillar: {{ salt.saltutil.runner('smoketests.pillar', minion=node, configuration='filestore2') }}
    - failhard: True
       
Save reset checklist {{ label }}:
  salt.runner:
    - name: smoketests.checklist
    - arg:
        - {{ node }}
        - 'filestore2'
    - failhard: True

Check reset OSDs {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.tests.migrate.check_osds
    - pillar: {{ salt.saltutil.runner('smoketests.pillar', minion=node, configuration='filestore2') }}
    - failhard: True

Migrate {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.redeploy.osds
    - pillar: {{ salt.saltutil.runner('smoketests.pillar', minion=node, configuration='bluestore') }}
    - failhard: True

Save checklist {{ label }}:
  salt.runner:
    - name: smoketests.checklist
    - arg:
        - {{ node }}
        - 'bluestore'
    - failhard: True

Check OSDs {{ label }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.tests.migrate.check_osds
    - pillar: {{ salt.saltutil.runner('smoketests.pillar', minion=node, configuration='bluestore') }}
    - failhard: True


