
{% for id in salt['osd.list']() %}

removing {{ id }}:
  module.run:
    - name: osd.remove
    - osd_id: {{ id }}

{% endfor %}

creating OSD:
  module.run:
    - name: osd.deploy

save grains:
  module.run:
    - name: osd.retain

