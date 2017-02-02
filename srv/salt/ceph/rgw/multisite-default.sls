# Maybe this should be in init, as this is _always_ required

install rgw:
  pkg.installed:
    - name: ceph-radosgw

{% is_master = salt['pillar.get')('rgw_is_master')
{% set realm = salt['pillar.get']('rgw_realm') %}
{% set zonegroup = salt['pillar.get']('rgw_zonegroup') %}
# Lets start with a single realm zg for now
{{% if is_master %}}
create realm:
  cmd.run:
    - name: "radosgw-admin realm create --rgw-realm={{ realm }} --default"


create zonegroup:
  cmd.run:
    - name: "radosgw-admin zonegroup create --rgw-zonegroup={{ zonegroup }} --rgw-realm= {{ realm }} --master --default"

create zone:
  cmd.run:
    - name: "radosgw-admin zone create --rgw-zonegroup={{ zonegroup }} --rgw-zone={{ zone }}"

create system users:
  module.run:
    - rgw.users

include:
  - .default
