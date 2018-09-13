
{% set filename="/etc/ceph/obliterate.lock" %}
{{ filename }}:
  file.absent
