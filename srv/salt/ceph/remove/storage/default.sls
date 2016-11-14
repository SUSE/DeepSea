
reweight nop:
  test.nop

{% for id in salt.saltutil.runner('rescinded.ids', cluster='ceph') %}

down id {{ id }}:
  module.run:
    - name: osd.down
    - id: {{ id }}

remove osd.{{ id }}:
  cmd.run:
    - name: "ceph osd crush remove osd.{{ id }}"

delete osd.{{ id }} key:
  cmd.run:
    - name: "ceph auth del osd.{{ id }}"

remove id {{ id }}:
  cmd.run:
    - name: "ceph osd rm {{ id }}"

{% endfor %}

