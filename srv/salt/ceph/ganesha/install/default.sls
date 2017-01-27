
install ganesha:
  cmd.run:
    - name: "zypper --non-interactive in nfs-ganesha nfs-ganesha-ceph nfs-ganesha-rgw"
    - shell: /bin/bash

