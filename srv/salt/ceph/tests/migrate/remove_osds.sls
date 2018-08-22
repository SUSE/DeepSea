
Removing OSDs:
  test.nop

{% for id in salt['osd.list']() %}

removing {{ id }}:
  module.run:
    - name: osd.remove
    - osd_id: {{ id }}
    - failhard: True

{% endfor %}


