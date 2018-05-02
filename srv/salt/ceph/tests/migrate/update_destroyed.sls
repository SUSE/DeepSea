
{% for id in salt['osd.list']() %}
{% set device = salt['osd.device'](id) %}

Update Destroyed {{ id }}:
  module.run:
    - name: osd.update_destroyed
    - device: {{ device }}
    - osd_id: '{{ id }}'
{% endfor %}
