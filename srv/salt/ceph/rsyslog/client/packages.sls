include:
{% if grains['os_family'] == 'Suse' %}
    - ceph/rsyslog/client/packages-suse
{% endif %}
