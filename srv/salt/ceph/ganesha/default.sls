
rpc:
  cmd.run:
    - name: "systemctl start rpcbind "
    - shell: /bin/bash

ganesha:
  cmd.run:
    - name: "/usr/bin/ganesha.nfsd -f /etc/ganesha/ceph.conf"
    - shell: /bin/bash

