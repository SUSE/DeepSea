include:
{% if grains['os_family'] == 'Suse' %}
    - ceph/rsyslog/server/packages-suse
{% endif %}
