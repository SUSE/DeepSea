{% for id in salt['osd.list']() %}
restart osd {{ id }}:
  cmd.run:
    - name: "systemctl restart ceph-osd@{{ id }}.service"
    - unless: "systemctl is-failed ceph-osd@{{ id }}.service"
    - fire_event: True
    - failhard: True
{% endfor %}
