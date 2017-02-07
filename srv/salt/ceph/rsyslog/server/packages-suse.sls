rsyslog_packages_clash_suse:
  pkg:
    - removed
    - names:
      - systemd-logger


rsyslog_packages_suse:
  pkg:
    - installed
    - names:
      - rsyslog
    - require:
      - pkg: rsyslog_packages_clash_suse
