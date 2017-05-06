
openattic nop:
  test.nop

{% if 'openattic' not in salt['pillar.get']('roles') %}

{% if salt['service.available']('openattic-systemd') %}
stop openattic-systemd:
  service.dead:
    - name: openattic-systemd
    - enable: False
{% endif %}

{% if salt['pillar.get']('openattic_configurations:drop_database', False) %}
{% if 'openattic' in salt['pkg.list_pkgs']() %}
remove openattic database:
  cmd.run:
    - names:
      - "su - postgres -c 'dropdb openattic'"
      - "su - postgres -c 'dropuser openattic'"
{% endif %}
{% endif %}

uninstall openattic:
  pkg.removed:
    - pkgs:
      - openattic
      - openattic-base
      - openattic-pgsql

{% for service in salt['pillar.get']('openattic_configurations:stop_services', []) %}
{% if salt['service.available'](service) %}
stop {{ service }}:
  service.dead:
    - name: {{ service }}
{% endif %}
{% endfor %}

include:
- .keyring

{% endif %}
