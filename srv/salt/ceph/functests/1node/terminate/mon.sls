{% set node = salt.saltutil.runner('select.first', roles='mon') %}

Shutdown monitor on {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.terminate.mon
    - failhard: True

Check process for ceph-mon:
  cmd.run:
    - name: "[ `pgrep -c ceph-mon` == 0 ]"
    - tgt: {{ node }}
    - shell: /bin/bash
    - failhard: True

Startup monitor on  {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.start.mon
    - failhard: True
