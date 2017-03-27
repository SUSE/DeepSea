
include:
  - .keyring

{% for device in salt['pillar.get']('storage:osds') %}
{% set dev = salt['cmd.run']('readlink -f ' + device ) %}
prepare {{ device }}:
  cmd.run:
    - name: "ceph-disk -v prepare --fs-type xfs --data-dev --journal-dev --cluster {{ salt['pillar.get']('cluster') }} --cluster-uuid {{ salt['pillar.get']('fsid') }} {{ device }}"
    - unless: "fsck {{ dev }}1"
    - fire_event: True

activate {{ device }}:
  cmd.run:
    - name: "ceph-disk -v activate --mark-init systemd --mount {{ dev }}1"
    - unless: "grep -q ^{{ dev }}1 /proc/mounts"
    - fire_event: True

{% endfor %}

{% for pair in salt['pillar.get']('storage:data+journals') %}
{% for data, journal in pair.items() %}
prepare {{ data }}:
  cmd.run:
    - name: "ceph-disk -v prepare --fs-type xfs --data-dev --journal-dev --cluster {{ salt['pillar.get']('cluster') }} --cluster-uuid {{ salt['pillar.get']('fsid') }} {{ data }} {{ journal }}"
    - unless: "fsck {{ data }}"
    - fire_event: True

activate {{ data }}:
  cmd.run:
    - name: "ceph-disk -v activate --mark-init systemd --mount {{ data }}1"
    - unless: "grep -q ^{{ data }} /proc/mounts"
    - fire_event: True

{% endfor %}
{% endfor %}

