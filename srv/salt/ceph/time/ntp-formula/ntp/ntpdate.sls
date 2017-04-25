{% from "ntp/map.jinja" import ntp with context %}

ntpdate:
  pkg.installed:
    - name: {{ ntp.ntpdate }}
