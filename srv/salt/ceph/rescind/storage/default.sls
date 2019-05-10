storage nop:
  test.nop

{% if 'storage' not in salt['pillar.get']('roles') %}

include:
- .keyring
{% endif %}
