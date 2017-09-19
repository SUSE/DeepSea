
nop:
  test.nop


{% for config in salt['pillar.get']('rgw_configurations') %}
{% if not salt['file.file_exists']("/srv/salt/ceph/configuration/files/" + config + ".conf") %}
{% set client = config + "." + grains['host'] %}
check {{ config }}:
  file.exists:
    - name: /srv/salt/ceph/configuration/files/ceph.conf.d/{{ config }}.conf
    - failhard: True
{% endif %}
{% endfor %}

