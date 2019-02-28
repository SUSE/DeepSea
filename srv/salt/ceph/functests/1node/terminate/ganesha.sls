{% set node = salt.saltutil.runner('select.first', roles='ganesha') %}

Shutdown ganesha on {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.terminate.ganesha
    - failhard: True

Check process for for nfs-ganesha:
  cmd.run:
    - name: "[ `pgrep -c nfs-ganesha` == 0 ]"
    - tgt: {{ node }}
    - shell: /bin/bash
    - failhard: True

Startup ganesha on  {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.start.ganesha
    - failhard: True
