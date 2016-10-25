{% for id in salt['osd.list']() %}
    wait {{ id }}:
      module.run:
       - name: wait.out
       - kwargs:
           'status': "HEALTH_ERR"
       - fire_event: True
       - failhard: True
     
    restart {{ id }}:
      cmd.run:
        - name: "systemctl restart ceph-osd@{{ id }}.service"
        - fire_event: True
{% endfor %}
