include:
{% if grains['os_family'] == 'Suse' %}
    - .packages-suse
{% endif %}
