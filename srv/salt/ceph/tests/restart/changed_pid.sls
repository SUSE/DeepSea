
Changed pid of ceph-{{ service }}:
  cmd.run:
    - name: "test \"$(pgrep ceph-{{ service }})\" != \"$(cat /tmp/restart.pid)\""
    - failhard: True
    - shell: /bin/bash

/tmp/restart.pid:
  file.absent


