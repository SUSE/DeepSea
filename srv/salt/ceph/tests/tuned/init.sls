{% set active_profile = salt['cmd.run']('tuned-adm active') %}
{% set roles = salt['pillar.get']('roles') %}

{% if 'storage' in roles %}

ses-osd is not active:
  cmd.run:
    - name: 'tuned-adm active | grep -q ses-osd'

fail if not ses-osd:
  test.fail_without_changes:
    - onlyif:
      - ses-osd is not active

{% elif 'mon' in roles %}

ses-mon is not active:
  cmd.run:
    - name: 'tuned-adm active | grep -q ses-mon'

fail if not ses-mon:
  test.fail_without_changes:
    - onlyif:
      - ses-mon is not active

{% elif 'mgr' in roles %}

ses-mgr is not active:
  cmd.run:
    - name: 'tuned-adm active | grep -q ses-mgr'

fail if not ses-mgr:
  test.fail_without_changes:
    - onlyif:
      - ses-mgr is not active

{% endif %}
