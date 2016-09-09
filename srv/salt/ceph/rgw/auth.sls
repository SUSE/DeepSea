

{% for rgw_node in salt.saltutil.runner('select.minions', host=True, cluster='ceph', roles='rgw') %}

# TODO allow multi rgw deployments on same node
{% set rgw_name = salt['pillar.get']('rgw_service_name', 'rgw')  %}
keyring {{ rgw_node }}:
  file.managed:
    - name: /var/lib/ceph/rgw/ceph-rgw.{{ grains['host'] }}/ceph.keyring
    - source:
      - salt://ceph/mds/files/keyring.j2
    - template: jinja
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True


add auth {{ rgw_node }}:
  cmd.run:
    - name: "ceph auth add client.{{ rgw_name }}.{{ grains['host'] }}  -i /var/lib/ceph/rgw/ceph-rgw.{{ grains['host'] }}/ceph.keyring"

{% endfor %}
