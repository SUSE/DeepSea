

ntp:
  pkg.installed:
    - pkgs:
      - ntp
    - order: 1

#ntp:
#  cmd.run:
#    - name: "zypper --non-interactive --no-gpg-checks in ntp"
#    - order: 1

include:
  - .ntp
