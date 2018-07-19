{% set roles = salt['pillar.get']('roles') %}
{% set mgr_off = pillar.get('tuned_mgr_init', 'default') %}
{% set mon_off = pillar.get('tuned_mon_init', 'default') %}

/etc/tuned/ceph-osd/tuned.conf:
  file.managed:
    - source: salt://ceph/tuned/files/ceph-osd/tuned.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644

{% if 'mgr' not in roles or 'default-off' not in mgr_off %}
{% if 'mon' not in roles or 'default-off' not in mon_off %}
start tuned:
  service.running:
    - name: tuned
    - enable: True

apply tuned ceph osd:
  # There's a bug with the tuned 'profile' state if the tuned is off
  # tuned.profile:
  #   - name: "ceph-osd"
  # Use cmd.run instead
  cmd.run:
    - name: 'tuned-adm profile ceph-osd'

{% endif %}
{% endif %}
