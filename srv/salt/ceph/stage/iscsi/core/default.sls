
{% set master = salt['master.minion']() %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}

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

iscsi apply:
  salt.state:
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.igw

{% for minion in salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}
add iscsi gateway {{ minion }} to dashboard:
  salt.function:
    - name: cmd.run
    - tgt: {{ master }}
    - tgt_type: compound
    - arg:
      - "ceph dashboard iscsi-gateway-add http://admin:admin@{{ minion }}:5000"
    - kwarg:
        unless: ceph dashboard iscsi-gateway-list | jq .gateways | grep -q "{{ minion }}:5000"
      
{% endfor %}

{% endif %}

