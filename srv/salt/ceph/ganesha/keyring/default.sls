{% for role in salt['ganesha.configurations']() %}

{% set keyring_name = "ceph.client." + role + "." + grains['host'] + ".keyring" %}
/etc/ceph/{{ keyring_name }}:
  file.managed:
    - source:
      - salt://ceph/ganesha/cache/{{ keyring_name }}
    - user: root
    - group: root
    - mode: 600
    - fire_event: True


{% set rgw_role = salt['rgw.configuration'](role) %}
{%if rgw_role %}
/etc/ceph/ceph.client.{{ rgw_role }}.{{ role + "." + grains['host'] }}.keyring:
  file.managed:
    - source:
      - salt://ceph/ganesha/cache/ceph.client.{{ rgw_role }}.{{ role + "." +  grains['host'] }}.keyring
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True

/etc/ceph/ceph.conf:
  file.append:
    - text: |
        [client.{{ rgw_role }}.{{ role + "." +  grains['host'] }}]
        keyring = /etc/ceph/ceph.client.{{ rgw_role }}.{{ role + "." + grains['host'] }}.keyring
    - fire_event: True

{% endif %}

{% endfor %}
