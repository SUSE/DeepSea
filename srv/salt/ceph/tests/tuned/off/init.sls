{% set osd_off = pillar.get('tuned_osd_init', 'default') %}
{% set mon_off = pillar.get('tuned_mon_init', 'default') %}
{% set mgr_off = pillar.get('tuned_mgr_init', 'default') %}
{% set roles = salt['pillar.get']('roles') %}
{% set active_profile = salt['cmd.run']('tuned-adm active') %}

{% if 'storage' in roles and 'default-off' in osd_off %}

tuned running on osd node:
  cmd.run:
    - name: 'pgrep -v tuned'

fail if some active profile for osd:
  test.fail_without_changes:
    - onlyif:
      - tuned running on osd node

{% endif %}

{% if 'mon' in roles and 'default-off' in mon_off %}

tuned running on mon node:
  cmd.run:
    - name: 'pgrep -v tuned'

fail if some active profile for mon:
  test.fail_without_changes:
    - onlyif:
      - tuned running on mon node

{% endif %}

{% if 'mgr' in roles and 'default-off' in mgr_off %}

tuned running on mgr node:
  cmd.run:
    - name: 'pgrep -v tuned'

fail if some active profile for mgr:
  test.fail_without_changes:
    - onlyif:
      - tuned running on mgr node

{% endif %}

{# In case no branch is taken #}
nop:
  test.nop
