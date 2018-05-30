
Changed pid:
  cmd.run:
    - name: "[ `pgrep ceph-{{ service }}` !=  `cat /tmp/restart.pid` ]"
    - shell: /bin/bash
    - failhard: True

/tmp/restart.pid:
  file.absent


