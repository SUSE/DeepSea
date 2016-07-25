
lrbd install:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks in lrbd"

lrbd:
  service.running:
    - name: lrbd
    - enable: True

reload:
  cmd.run:
    - name: "lrbd"
    - shell: /bin/bash

