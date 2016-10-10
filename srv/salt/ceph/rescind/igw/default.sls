
igw nop:
  test.nop

{% if 'igw' not in salt['pillar.get']('roles') %}
stop lrbd:
  service.dead:
    - name: lrbd
    - enable: False

uninstall lrbd:
  pkg.removed:
    - name: lrbd
    - onlyif: "test -f /usr/sbin/lrbd"

include:
- .keyring
- .sysconfig
{% endif %}
