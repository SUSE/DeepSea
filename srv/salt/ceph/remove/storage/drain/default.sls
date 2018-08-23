
drain nop:
  test.nop

{% for id in salt.saltutil.runner('rescinded.ids') %}
drain osd.{{ id }}:
  module.run:
    - name: osd.zero_weight
    - osd_id: {{ id }}

set osd {{ id }} out:
  cmd.run:
    - name: "ceph osd out {{ id }}"

{% endfor %}

