{% set role = salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{% set node = salt.saltutil.runner('select.first', roles=role[0]) %}

Shutdown radosgw on {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.terminate.rgw
    - failhard: True

Check process for radosgw:
  cmd.run:
    - name: "[ `pgrep -c radosgw` == 0 ]"
    - tgt: {{ node }}
    - shell: /bin/bash
    - failhard: True

Startup radosgw on  {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.start.rgw
    - failhard: True
