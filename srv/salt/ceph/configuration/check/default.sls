
nop:
  test.nop

{% for config in salt['pillar.get']('rgw_configurations') %}
{% set client = config + "." + grains['host'] %}
check {{ config }}:
  file.exists:
    - name: /srv/salt/ceph/configuration/files/ceph.conf.d/{{ config }}.conf
    - failhard: True

{% endfor %}

