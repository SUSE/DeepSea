
nfs:
  cmd.run:
    - name: "systemctl start nfs "
    - shell: /bin/bash
rpc:
  cmd.run:
    - name: "systemctl start rpcbind "
    - shell: /bin/bash

rpc-statd:
  cmd.run:
    - name: "systemctl start rpc-statd "
    - shell: /bin/bash

ganesha:
  cmd.run:
    - name: "systemctl start nfs-ganesha"
    - shell: /bin/bash
