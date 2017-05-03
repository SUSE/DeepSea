
include:
  - .keyring

{% for device in salt['osd.configured']() %}
prepare {{ device }}:
  cmd.run:
    - name: {{ salt['osd.prepare'](device) }}
    - unless: {{ salt['osd.is_prepared'](device) }}
    - fire_event: True

activate {{ device }}:
  cmd.run:
    - name: {{ salt['osd.activate'](device) }}
    - unless: {{ salt['osd.is_activated'](device) }}
    - fire_event: True
{% endfor %}

save grains:
  module.run:
    - name: osd.retain

