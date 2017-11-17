include:
{% if grains.get('os_family', '') == 'Suse' %}
  - .kernel
{% endif %}
  - .regular
