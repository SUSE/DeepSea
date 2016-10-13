

{% if not salt['mine.get'](tgt='*', fun='roles.igw') %}

wipe configuration:
  cmd.run:
    - name: ". /etc/sysconfig/lrbd; /usr/sbin/lrbd $LRBD_OPTIONS -W || :"
    - shell: /bin/bash
    - onlyif: "test -f /usr/sbin/lrbd"

{% endif %}

stop lrbd:
  service.dead:
    - name: lrbd
    - enable: False

uninstall lrbd:
  pkg.removed:
    - name: lrbd
    - onlyif: "test -f /usr/sbin/lrbd"

