
{% for id in salt['osd.list']() %}

stopping {{ id }}:
  module.run:
    - name: osd.terminate
    - osd_id: {{ id }}

{% endfor %}

