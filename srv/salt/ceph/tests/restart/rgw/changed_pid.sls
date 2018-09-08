
Changed pid of radosgw:
  cmd.run:
    - name: "test \"$(pgrep radosgw)\" != \"$(cat /tmp/restart.pid)\""
    - failhard: True
    - shell: /bin/bash

/tmp/restart.pid:
  file.absent


