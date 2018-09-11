
Save pid of radosgw:
  cmd.run:
    - name: "pgrep radosgw > /tmp/restart.pid"
    - failhard: True
    - shell: /bin/bash

Assert pid of radosgw really was determined:
  cmd.run:
    - name: "test -s /tmp/restart.pid"
    - failhard: True

