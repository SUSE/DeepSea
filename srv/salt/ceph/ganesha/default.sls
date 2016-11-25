
nfs:
  cmd.run:
    - name: "systemctl start nfs "
    - shell: /bin/bash
rpc:
  cmd.run:
    - name: "systemctl start rpcbind "
    - shell: /bin/bash

rpc:
  cmd.run:
    - name: "systemctl start rpc-statd "
    - shell: /bin/bash

ganesha:
  cmd.run:
    - name: "/usr/bin/ganesha.nfsd -f /etc/ganesha/ceph.conf -L /var/log/ganesha.log"
    - shell: /bin/bash

