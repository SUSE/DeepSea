
{% set device = salt['osd.device'](1) %}

Update Destroyed:
  module.run:
    - name: osd.update_destroyed
    - device: {{ device }}
    - osd_id: '1'
