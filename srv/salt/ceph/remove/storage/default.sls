
reweight nop:
  test.nop

{% for id in salt.saltutil.runner('rescinded.ids', cluster='ceph') %}
clear osd.{{ id }}:
  module.run:
    - name: osd.zero_weight
    - id: {{ id }}

down id {{ id }}:
  cmd.run:
    - name: "ceph osd down {{ id }}"

remove osd.{{ id }}:
  cmd.run:
    - name: "ceph osd crush remove osd.{{ id }}"

delete osd.{{ id }} key:
  cmd.run:
    - name: "ceph auth del osd.{{ id }}"

remove id {{ id }}:
  module.run:
    - name: retry.cmd
    - kwargs:
        cmd: "ceph osd rm {{ id }}"

{% endfor %}

