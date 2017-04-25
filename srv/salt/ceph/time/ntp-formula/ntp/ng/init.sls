# Include :download:`map file <map.jinja>` of OS-specific package names and
# file paths. Values can be overridden using Pillar.
{% from "ntp/ng/map.jinja" import ntp with context %}
{% set service = {True: 'running', False: 'dead'} %}

{% if 'package' in ntp.lookup %}
ntp:
  pkg.installed:
    - name: {{ ntp.lookup.package }}
{% endif %}

{% if 'ntp_conf' in ntp.lookup %}
ntpd_conf:
  file.managed:
    - name: {{ ntp.lookup.ntp_conf }}
    - source: salt://ntp/ng/files/ntp.conf
    - template: jinja
    - context:
      config: {{ ntp.settings.ntp_conf }}
    - watch_in:
      - service: {{ ntp.lookup.service }}
    {% if 'package' in ntp.lookup %}
    - require:
      - pkg: ntp
    {% endif %}
{% endif %}

{% if 'ntpd' in ntp.settings %}
ntpd:
  service.{{ service.get(ntp.settings.ntpd) }}:
    - name: {{ ntp.lookup.service }}
    - enable: {{ ntp.settings.ntpd }}
    {% if 'provider' in ntp.lookup %}
    - provider: {{ ntp.lookup.provider }}
    {% endif %}
    {% if 'package' in ntp.lookup %}
    - require:
      - pkg: ntp
    {% endif %}
    - watch:
      - file: ntpd_conf
{% endif %}
