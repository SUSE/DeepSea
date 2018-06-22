{% set roles = salt['pillar.get']('roles') %}
{% set mgr_off = pillar.get('tuned_mgr_init', 'default') %}

/etc/tuned/ses-mon/tuned.conf:
  file.managed:
    - source: salt://ceph/tuned/files/ses-mon/tuned.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644

{% if 'mgr' not in roles or 'default-off' not in mgr_off %}
start tuned:
  service.running:
    - name: tuned
    - enable: True

apply tuned ses mon:
  cmd.run:
    - name: 'tuned-adm profile ses-mon'

{% endif %}