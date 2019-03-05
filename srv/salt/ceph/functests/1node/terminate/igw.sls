{% set node = salt.saltutil.runner('select.first', roles='igw') %}

Shutdown igw on {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.terminate.igw
    - failhard: True

Check process for targetcli:
  cmd.run:
    - name: "[ `targetcli ls| grep -c TPG` == 0 ]"
    - tgt: {{ node }}
    - shell: /bin/bash
    - failhard: True

Startup igw on  {{ node }}:
  salt.state:
    - tgt: {{ node }}
    - sls: ceph.start.igw
    - failhard: True
