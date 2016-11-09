include:
{% if grains['os_family'] == 'Suse' %}
    - ceph.iperf.packages-suse
{% endif %}
