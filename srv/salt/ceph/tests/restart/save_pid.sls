
Save pid of ceph-{{ service }}:
  cmd.run:
    - name: "pgrep ceph-{{ service }} > /tmp/restart.pid"
    - failhard: True
    - shell: /bin/bash

Assert pid of ceph-{{ service }} really was determined:
  cmd.run:
    - name: "test -s /tmp/restart.pid"
    - failhard: True

