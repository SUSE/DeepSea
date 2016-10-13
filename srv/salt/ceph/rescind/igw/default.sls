
igw nop:
  test.nop

{% if 'igw' not in salt['pillar.get']('roles') %}

include:
- .lrbd
- .keyring
- .sysconfig

{% endif %}
