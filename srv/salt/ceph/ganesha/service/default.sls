start-nfs:
  cmd.run:
    - name: "systemctl start nfs "
    - shell: /bin/bash

enable-nfs:
  cmd.run:
    - name: "systemctl enable nfs "
    - shell: /bin/bash

start-rpc:
  cmd.run:
    - name: "systemctl start rpcbind "
    - shell: /bin/bash

enable-rpc:
  cmd.run:
    - name: "systemctl enable rpcbind "
    - shell: /bin/bash

start-statd:
  cmd.run:
    - name: "systemctl start rpc-statd "
    - shell: /bin/bash

enable-rpc-statd:
  cmd.run:
    - name: "systemctl enable rpc-statd "
    - shell: /bin/bash

start-ganesha:
  cmd.run:
    - name: "systemctl start nfs-ganesha"
    - shell: /bin/bash

enable-ganesha:
  cmd.run:
    - name: "systemctl enable nfs-ganesha"
    - shell: /bin/bash
