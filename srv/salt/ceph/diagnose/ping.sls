{% for touple in salt.saltutil.runner('nettest.minion_link_ipv4_parallel', cluster='ceph') %}
{% set minion_list = touple[0] %}
{% set addr = touple[1] %}
ping {{ loop }}:
  salt.function:
    - tgt: 'L@{{ minion_list }}'
    - tgt_type: compound
    - name: cmd.run
    - arg :
      - 'ping -c 4 {{ addr }}'
{% endfor %}
