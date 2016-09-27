

include:
  - .keyring
  - .partition

{% for device in salt['pillar.get']('storage:osds') %}
prepare {{ device }}:
  cmd.run:
    - name: "ceph-disk -v prepare --fs-type xfs --data-dev --journal-dev --cluster {{ salt['pillar.get']('cluster') }} --cluster-uuid {{ salt['pillar.get']('fsid') }} {{ device }}2 {{ device }}1"
    - unless: "fsck {{ device }}2"
    - fire_event: True

activate {{ device }}:
  cmd.run:
    - name: "ceph-disk -v activate --mark-init systemd --mount {{ device }}2"
    - unless: "grep -q ^{{ device }}2 /proc/mounts"
    - fire_event: True

{% endfor %}

{% for pair in salt['pillar.get']('storage:data+journals') %}
{% for data, journal in pair.items() %}
prepare {{ data }}:
  cmd.run:
    - name: "ceph-disk -v prepare --fs-type xfs --data-dev --journal-dev --cluster {{ salt['pillar.get']('cluster') }} --cluster-uuid {{ salt['pillar.get']('fsid') }} {{ data }} {{ journal }}"
    - unless: "fsck {{ data }}"
    - fire_event: True

activate {{ device }}:
  cmd.run:
    - name: "ceph-disk -v activate --mark-init systemd --mount {{ data }}"
    - unless: "grep -q ^{{ data }} /proc/mounts"
    - fire_event: True

{% endfor %}
{% endfor %}


