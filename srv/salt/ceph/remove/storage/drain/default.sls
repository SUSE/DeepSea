
reweight nop:
  test.nop

{% for id in salt.saltutil.runner('rescinded.ids', cluster='ceph') %}
drain osd.{{ id }}:
  module.run:
    - name: osd.zero_weight
    - id: {{ id }}

set osd {{ id }} out:
  cmd.run:
    - name: "ceph osd out {{ id }}"

{% endfor %}

