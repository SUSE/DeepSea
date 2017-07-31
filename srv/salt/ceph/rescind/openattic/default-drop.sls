
openattic nop:
  test.nop

{% if 'openattic' not in salt['pillar.get']('roles') %}

{% if salt['service.available']('openattic-systemd') %}
stop openattic-systemd:
  service.dead:
    - name: openattic-systemd
    - enable: False
{% endif %}

{% if 'openattic' in salt['pkg.list_pkgs']() %}
remove openattic database:
  cmd.run:
    - names:
      - "su - postgres -c 'dropdb openattic; dropuser openattic;'"
{% endif %}

uninstall openattic:
  pkg.removed:
    - pkgs:
      - openattic

{% for service in [ 'apache2', 'postgresql' ] %}
{% if salt['service.available'](service) %}
stop {{ service }}:
  service.dead:
    - name: {{ service }}
{% endif %}
{% endfor %}

include:
- .keyring

{% endif %}
