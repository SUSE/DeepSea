{% set node = salt.saltutil.runner('select.first', roles='mgr') %}

Shutdown mgr on {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.terminate.mgr
    - failhard: True

Check process for ceph-mgr:
  cmd.run:
    - name: "[ `pgrep -c ceph-mgr` == 0 ]"
    - tgt: {{ node }}
    - shell: /bin/bash
    - failhard: True

Startup mgr on  {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.start.mgr
    - failhard: True
