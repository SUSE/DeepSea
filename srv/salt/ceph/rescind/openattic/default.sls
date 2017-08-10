
openattic nop:
  test.nop

{% if 'openattic' not in salt['pillar.get']('roles') %}

{% if salt['service.available']('openattic-systemd') %}
stop openattic-systemd:
  service.dead:
    - name: openattic-systemd
    - enable: False
{% endif %}

uninstall openattic:
  pkg.removed:
    - pkgs:
      - openattic

{% for service in [ 'postgresql' ] %}
{% if salt['service.available'](service) %}
stop {{ service }}:
  service.dead:
    - name: {{ service }}
{% endif %}
{% endfor %}

include:
- .keyring

{% endif %}
