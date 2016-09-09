{% set cluster = salt['pillar.get']('cluster') %}
# copying the same id rgw_host from auth would have from runner
{% set rgw_id = salt['pillar.get']('rgw_service_name','rgw')+'.'+salt['grains.get']('id').split('.')[0] %}
{% set rgw_data_dir = salt['pillar.get']('rgw_data','/var/lib/ceph/radosgw/' + cluster + '-' + rgw_instance) %}

{{ rgw_data_dir }}/keyring:
  file.managed:
    - source:
      - salt://ceph/rgw/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - fire_event: True
    - context:
        rgw_node: {{ rgw_instance }}
