
{% set kernel= grains['kernelrelease'] | replace('-default', '')  %}

{% set latest = salt['cmd.run']('rpm -q --last kernel-default | head -1', shell="/bin/bash" ) %}

{% if kernel in latest %}
{% set matches = "true" %}
{% else %}
{% set matches = "false" %}
{% endif %}
anything:
  cmd.run:
    - name: "echo {{ matches }} "
