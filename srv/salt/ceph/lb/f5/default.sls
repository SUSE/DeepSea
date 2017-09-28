{% for lb_name in salt['pillar.get']('f5') %}
{% set lb = salt['pillar.get']('f5')[lb_name] %}

add_rgw_pool_member_to_{{ lb_name }}:
  bigip.add_pool_member:
    - hostname: {{ lb['mgmt_ip']}}
    - username: {{ lb['user'] }}
    - password: {{ lb['password'] }}
    - name: ~{{ lb['partition'] }}~{{ lb['pool'] }}
    - member:
         name: {{ pillar['public_address'] }}%{{ lb['routing_domain'] }}:80
         partition: {{ lb['partition'] }}
{% endfor %}
