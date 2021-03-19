{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}

{% set master = salt['master.minion']() %}

{% set iscsi_username = pillar.get('ceph_iscsi_username', 'admin') %}
{% set iscsi_password = pillar.get('ceph_iscsi_password', 'admin') %}
{% set iscsi_port = pillar.get('ceph_iscsi_port', '5000') %}
{% set iscsi_ssl = pillar.get('ceph_iscsi_ssl', True) %}

remove iscsi gateways:
  salt.function:
    - name: cmd.run
    - tgt: {{ master }}
    - tgt_type: compound
    - arg:
      - "for i in `ceph dashboard iscsi-gateway-list | jq -r '.gateways | to_entries[].key'`; do ceph dashboard iscsi-gateway-rm $i; done"

{% for igw_address in salt.saltutil.runner('select.minions', roles='igw', cluster='ceph', host=True, fqdn=True) %}

{% if iscsi_ssl %}
{% set iscsi_url = "https://" + iscsi_username + ":" + iscsi_password + "@" + igw_address + ":" + iscsi_port %}
{% else %}
{% set iscsi_url = "http://" + iscsi_username + ":" + iscsi_password + "@" + igw_address + ":" + iscsi_port %}
{% endif %}

add iscsi gateway {{ igw_address }} to dashboard:
  salt.function:
    - name: cmd.run
    - tgt: {{ master }}
    - tgt_type: compound
    - arg:
      - "echo -n {{ iscsi_url }} | ceph dashboard iscsi-gateway-add -i -"
    - kwarg:
        unless: ceph dashboard iscsi-gateway-list | jq .gateways | grep -q "{{ igw_address }}:{{ iscsi_port }}"

{% endfor %}

{% endif %}