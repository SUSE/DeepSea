
{% set device_count = salt['cephdisks.filter']() | length %}
Device count {{ device_count }} at {{ salt['status.time']('%s') }}:
  test.nop
{% if device_count < 4 %}
Skipping, not enough devices:
  test.fail_without_changes
{% endif %}
