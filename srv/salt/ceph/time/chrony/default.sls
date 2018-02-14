
{% set time_server = salt['pillar.get']('time_server') %}
{% if time_server is string %}
{% set time_server = [time_server] %}
{% endif %}

{% if grains['id'] not in salt['pillar.get']('time_server') %}

include:
  - ...rescind.time.ntp

install chrony:
  pkg.installed:
    - pkgs:
      - chrony
    - refresh: True
    - fire_event: True

service_reload:
  module.run:
    - name: service.systemctl_reload

/etc/chrony.conf:
  file.managed:
    - source:
        - salt://ceph/time/chrony/files/chrony.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - backup: minion
    - fire_event: True

start chronyd:
  service.running:
    - name: chronyd
    - enable: True
    - fire_event: True

{% endif %}

prevent empty file:
  test.nop
