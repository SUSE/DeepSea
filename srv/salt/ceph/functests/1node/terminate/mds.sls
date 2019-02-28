{% set node = salt.saltutil.runner('select.first', roles='mds') %}

Shutdown mds on {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.terminate.mds
    - failhard: True

Check process for ceph-mds:
  cmd.run:
    - name: "[ `pgrep -c ceph-mds` == 0 ]"
    - tgt: {{ node }}
    - shell: /bin/bash
    - failhard: True

Startup mds on  {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.start.mds
    - failhard: True
