###############################
###### Salt State For NTP #####
###############################

### Designed for use specifically with CentOS 5.X and 6.X ###
### Built when CentOS 5.9 and 6.4 were the current versions ###
### See pillardata/ntp.sls for example data that would go in pillar ###

# NTP Packages
ntp-pkgs:
  pkg.installed:
    - names:
      - ntp
      - tzdata

# Install and run ntpdate at boot on CentOS 6.X
# Remember ntpdate only runs at boot time - ntpd takes
# care of things after
{% if grains['osrelease'][0] == '6' %}
ntpdate:
  pkg:
    - installed
    - require:
      - pkg: ntp-pkgs
  service:
    - enabled
{% endif %}

# NTP Service
ntpd:
  service.running:
    - enable: True
    - watch:
      - file: /etc/ntp.conf
      - pkg: ntp-pkgs

# NTP Configuration File
/etc/ntp.conf:
  file.managed:
    - user: root
    - group: root
    - mode: '0440'
    - template: jinja
    - source: salt://ntp/local_server/files/ntp.CentOS.{{ grains['osrelease'][0] }}.conf
    - defaults:
        comment: "{{ pillar['ntp']['comment'] }}"
        localnetworks: {{ pillar['ntp']['localnetworks'] }}
        ntpservers: {{ pillar['ntp']['ntpservers'] }}
    - require:
      - pkg: ntp-pkgs
