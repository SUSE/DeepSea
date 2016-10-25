{% for id in salt['osd.list']() %}
    restart osd #{{ id }}:
      cmd.run:
        - name: "systemctl restart ceph-osd@{{ id }}.service"
        - unless: "systemctl status ceph-osd@{{ id }}.service | grep -q '^Active: failed'" 
        - fire_event: True
        - failhard: True
{% endfor %}
