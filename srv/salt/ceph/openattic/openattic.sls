

openattic:
  pkg.installed:
    - pkgs:
      - openattic
      - openattic-gui

#install openattic:
#  cmd.run:
#    - name: "zypper --non-interactive --no-gpg-checks in openattic openattic-gui"

configure openattic:
  cmd.run:
    - name: "oaconfig install --allow-broken-hostname"


