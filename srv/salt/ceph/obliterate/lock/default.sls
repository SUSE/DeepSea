
{% set filename="/etc/ceph/obliterate.lock" %}
{% if salt['file.file_exists'](filename) %}
Run 'ceph.obliterate.unlock' to continue:
  test.fail_without_changes
{% else %}
{{ filename }}:
  file.touch
{% endif %}
