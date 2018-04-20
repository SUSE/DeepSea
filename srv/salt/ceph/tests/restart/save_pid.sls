
Save pid:
  cmd.run:
    - name: "pgrep ceph-{{ service }} > /tmp/restart.pid"
    - shell: /bin/bash

