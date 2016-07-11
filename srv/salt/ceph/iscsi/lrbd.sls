
lrbd install:
  pkg.installed:
    - name: lrbd

lrbd:
  service.running:
    - name: lrbd
    - enable: True

reload:
  cmd.run:
    - name: "lrbd"
    - shell: /bin/bash

