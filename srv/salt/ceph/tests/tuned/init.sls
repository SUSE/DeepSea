{% set active_profile = salt['cmd.run']('tuned-adm active') %}
{% set roles = salt['pillar.get']('roles') %}

{% if 'storage' in roles %}

ceph-osd is not active:
  cmd.run:
    - name: 'tuned-adm active | grep -q ceph-osd'

fail if not ceph-osd:
  test.fail_without_changes:
    - onlyif:
      - ceph-osd is not active

{% elif 'mon' in roles %}

ceph-mon is not active:
  cmd.run:
    - name: 'tuned-adm active | grep -q ceph-mon'

fail if not ceph-mon:
  test.fail_without_changes:
    - onlyif:
      - ceph-mon is not active

{% elif 'mgr' in roles %}

ceph-mgr is not active:
  cmd.run:
    - name: 'tuned-adm active | grep -q ceph-mgr'

fail if not ceph-mgr:
  test.fail_without_changes:
    - onlyif:
      - ceph-mgr is not active

{% endif %}
