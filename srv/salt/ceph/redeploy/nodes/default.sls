
{% for id in salt['osd.list']() %}
setting osd.{{ id }} weight to zero:
  module.run:
    - name: osd.zero_weight
    - id: {{ id }}
    - wait: False
{% endfor %}

redeploy:
  module.run:
    - name: osd.redeploy
    - simultaneous: True

