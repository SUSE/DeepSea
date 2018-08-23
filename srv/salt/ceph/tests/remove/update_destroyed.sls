
{% set device = salt['osd.device'](0) %}

Update Destroyed:
  module.run:
    - name: osd.update_destroyed
    - device: {{ device }}
    - osd_id: '0'
