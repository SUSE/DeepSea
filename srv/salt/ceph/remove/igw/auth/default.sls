
{% set client = "client.igw." + grains['host'] %}

deauth {{ client }}:
  cmd.run:
    - name: "ceph auth del {{ client }}"

