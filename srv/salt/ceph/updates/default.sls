include:
{% if grains.get('os_family', '') == 'Suse' and pillar.get('kernel_update', True) %}
  - .kernel
{% endif %}
  - .regular
