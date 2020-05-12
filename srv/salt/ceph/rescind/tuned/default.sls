prevent empty rendering:
  test.nop:
    - name: skip

{% set roles = salt['pillar.get']('roles') %}

{% if roles == [] %}

uninstall tuned:
  pkg.removed:
    - name: tuned

{% endif %}
