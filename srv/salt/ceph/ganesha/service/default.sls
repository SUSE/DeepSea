start-ganesha:
  cmd.run:
    - name: "systemctl restart nfs-ganesha"
    - shell: /bin/bash

enable-ganesha:
  cmd.run:
    - name: "systemctl enable nfs-ganesha"
    - shell: /bin/bash
