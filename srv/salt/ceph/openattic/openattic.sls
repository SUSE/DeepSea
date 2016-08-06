
install openattic:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks in openattic"

configure openattic:
  cmd.run:
    - name: "oaconfig install --allow-broken-hostname"


