
{% set master = salt['master.minion']() %}

{% set igw_minions = salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}
{% if igw_minions %}

set igw_service_daemon pillar item:
  salt.runner:
    - name: iscsi_upgrade.set_igw_service_daemon
    - failhard: True

add_mine_cephimages.list_function:
  salt.function:
    - name: mine.send
    - arg:
      - cephimages.list
    - tgt: {{ master }}
    - tgt_type: compound

{% set rbd_pool = salt['master.find_pool']('rbd', 'iscsi-images') %}

{% if not rbd_pool %}
{% set rbd_pool = "iscsi-images" %}

create configs pool:
  salt.function:
    - name: cmd.run
    - tgt: {{ master }}
    - tgt_type: compound
    - arg:
      - "ceph osd pool create iscsi-images 128 && ceph osd pool application enable iscsi-images rbd"
    - kwarg:
        unless: "ceph osd pool ls | grep -q iscsi-images$"

{% endif %}

create igw config:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.igw.config.create_iscsi_config
    - failhard: True
    - pillar:
        iscsi-pool: {{ rbd_pool }}

clear salt file server file list cache:
  salt.runner:
    - name: fileserver.clear_file_list_cache

apply igw config:
  salt.state:
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.igw.config.apply_iscsi_config
    - failhard: True

auth:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.igw.auth

keyring:
  salt.state:
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.igw.keyring

{% for igw_minion in igw_minions %}
# We need to perform this step sequentially in each minion
# to avoid the downtime of the iSCSI service in case of
# an upgrade

install and start ceph-iscsi in {{ igw_minion }}:
  salt.state:
    - tgt: {{ igw_minion }}
    - sls: ceph.igw
    - failhard: True

wait for iscsi gateway {{ igw_minion }}:
  salt.function:
    - name: iscsi.wait_for_gateway
    - tgt: {{ igw_minion }}
    - failhard: True

{% endfor %}

{% set iscsi_username = pillar.get('ceph_iscsi_username', 'admin') %}
{% set iscsi_password = pillar.get('ceph_iscsi_password', 'admin') %}
{% set iscsi_port = pillar.get('ceph_iscsi_port', '5000') %}
{% set iscsi_ssl = pillar.get('ceph_iscsi_ssl', False) %}

{% if iscsi_ssl %}
disable dashboard ssl verification:
  salt.function:
    - name: cmd.run
    - tgt: {{ master }}
    - tgt_type: compound
    - kwarg:
        cmd: ceph dashboard set-iscsi-api-ssl-verification false
        shell: /bin/bash
    - failhard: True
{% endif %}

{% for igw_address in salt.saltutil.runner('select.public_addresses', roles='igw', cluster='ceph', url=True) %}

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
      - "ceph dashboard iscsi-gateway-add {{ iscsi_url }}"
    - kwarg:
        unless: ceph dashboard iscsi-gateway-list | jq .gateways | grep -q "{{ igw_address }}:{{ iscsi_port }}"

{% endfor %}

{% endif %}

