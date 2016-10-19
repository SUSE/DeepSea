{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage', host=True) %}

    {% for device in salt['pillar.get']('storage:osds') %}
        wait {{ host }}-{{ device }}:
          module.run:
           - name: wait.out
           - kwargs:
               'status': "HEALTH_ERR"
           - fire_event: True
           - failhard: True
         
        restart {{ host }}-{{device}}:
          cmd.run:
            - name: "systemctl restart ceph-osd@{{ device }}.service"
            - fire_event: True
    {% endfor %}
{% endfor %}
