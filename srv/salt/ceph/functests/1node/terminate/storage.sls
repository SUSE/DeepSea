
{% set node = salt.saltutil.runner('select.first', roles='storage') %}

Shutdown storage on {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.terminate.storage
    - failhard: True

Check process:
  cmd.run:
    - name: "[ `pgrep -c ceph-osd` == 0 ]"
    - tgt: {{ node }}
    - shell: /bin/bash
    - failhard: True

Startup storage on  {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.start.storage
    - failhard: True
