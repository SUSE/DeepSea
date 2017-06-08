
storage nop:
  test.nop

{% if 'storage' not in salt['pillar.get']('roles') %}

{% for id in salt['osd.list']() %}

removing {{ id }}:
  module.run:
    - name: osd.remove
    - osd_id: {{ id }}
    - kwargs:
        force: True

{% endfor %}

include:
- .keyring
{% endif %}
