{% if 'storage' in salt['pillar.get']('roles') %}

 invoking osd.takeover:
  module.run:
    - name: osd.takeover
    - fire_event: True
    - failhard: True

 {% else %}

 no osd detected:
  test.nop

 {% endif %}
