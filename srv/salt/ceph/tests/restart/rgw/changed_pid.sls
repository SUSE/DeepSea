
Changed pid:
  cmd.run:
    - name: "[ `pgrep radosgw` !=  `cat /tmp/restart.pid` ]"
    - shell: /bin/bash
    - failhard: True

/tmp/restart.pid:
  file.absent


