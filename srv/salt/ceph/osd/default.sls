
include:
  - .keyring
{% set bluestore = salt['pillar.get']('bluestore') %}
{% set dmcrypt = salt['pillar.get']('dmcrypt') %}
{% set base_cmd = "ceph-disk -v prepare" %}
{% set cluster_ident = "--cluster {{ salt['pillar.get']('cluster') }}" %}
{% set cluster_uuid = "--cluster-uuid {{ salt['pillar.get']('fsid') }}" %}
{% set data_and_journal = "--data-dev --journal-dev" %}
{% set fstype = "xfs" %}

{% if dmcrypt %}
   {% set base_cmd = {{ base_cmd }} --dmcrypt %}
{% if bluestore %}
   {% set cmd = {{ base_cmd }} --bluestore {{ data_and_journal }} {{ cluster_ident }} {{ cluster_uuid }} %}
{% else %}
   {% set cmd = {{ base_cmd }} --fs-type {{ fstype }} {{ data_and_journal }} {{ cluster_ident }} {{ cluster_uuid }} %}
{% endif %}

{% for device in salt['pillar.get']('storage:osds') %}
{% set dev = salt['cmd.run']('readlink -f ' + device ) %}
prepare {{ device }}:
  cmd.run:
    - name: {{ cmd }} {{ device }}"
    - unless: "fsck {{ dev }}1"
    - fire_event: True

{% if not dmcrypt %}

activate {{ device }}:
  cmd.run:
    - name: "ceph-disk -v activate --mark-init systemd --mount {{ dev }}1"
    - unless: "grep -q ^{{ dev }}1 /proc/mounts"
    - fire_event: True

{% endif %}

{% endfor %}

{% for pair in salt['pillar.get']('storage:data+journals') %}
{% for data, journal in pair.items() %}


prepare {{ data }}:
  cmd.run:
    - name: "{{ cmd }} { data }} {{ journal }}"
    - unless: "fsck {{ data }}"
    - fire_event: True

{% if not dmcrypt %}

activate {{ data }}:
  cmd.run:
    - name: "ceph-disk -v activate --mark-init systemd --mount {{ data }}"
    - unless: "grep -q ^{{ data }} /proc/mounts"
    - fire_event: True

{% endif %}

{% endfor %}
{% endfor %}

