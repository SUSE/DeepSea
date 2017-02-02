# Maybe this should be in init, as this is _always_ required

install rgw:
  pkg.installed:
    - name: ceph-radosgw

{% is_master = salt['pillar.get')('rgw_is_master')
{% set realm = salt['pillar.get']('rgw_realm') %}
{% set zonegroup = salt['pillar.get']('rgw_zonegroup') %}
{% set master_url = salt['pillar.get']('rgw_master_url') %}
{% set access = salt['pillar.get']('rgw_system_access_key') %}
{% set secret = salt['pillar.get']('rgw_system_secret_key') %}
# Lets start with a single realm zg for now
create realm:
  cmd.run:
    {{% if is_master %}}
    - name: "radosgw-admin realm create --rgw-realm={{ realm }} --default"
    {{% else %}}
    - name: "radosgw-admin realm pull --url={{ master_url }} --access_key={{ access }} --secret={{ secret }}"
    {{% endif %}}

default realm:
  cmd.run:
    - name: "radosgw-admin realm default --rgw-realm={{ realm }}"
    - require: create realm

create zonegroup:
  cmd.run:
    - name: "radosgw-admin zonegroup create --rgw-zonegroup={{ zonegroup }} --rgw-realm= {{ realm }} --master --default"
    - require: create realm
    - unless: "radosgw-admin zonegroup get --rgw-zonegroup={{ zonegroup }}"

create zone:
  cmd.run:
    - name: "radosgw-admin zone create --rgw-zonegroup={{ zonegroup }} --rgw-zone={{ zone }} --access-key={{ access }} --secret={{ secret }} --default"
    - require: create zonegroup

{{% if is_master %}}
create system users:
  module.run:
    - rgw.users
    - require: create zone
{{% endif %}}

include:
  - .default
