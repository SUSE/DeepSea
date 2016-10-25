{% for id in salt['osd.list']() %}
   wait until osd #{{ id }} can be restarted: 
      module.run:
       - name: wait.out
       - kwargs:
           'status': "HEALTH_ERR"
       - fire_event: True
       - failhard: True
     
    restart osd #{{ id }}:
      cmd.run:
        - name: "systemctl restart ceph-osd@{{ id }}.service"
        - fire_event: True
{% endfor %}
