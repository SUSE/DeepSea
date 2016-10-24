wait:
  module.run:
   - name: wait.out
   - kwargs:
       'status': "HEALTH_ERR"
   - fire_event: True
   - failhard: True

restart:
  cmd.run:
    - name: "lrbd"
    - fire_event: True

{% endfor %}
