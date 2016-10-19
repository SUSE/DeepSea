
ntp:
  pkg.installed:
    - pkgs:
      - ntp

sync time:
  cmd.run:
    - name: "sntp -S -c {{ salt['pillar.get']('time_server') }}"
