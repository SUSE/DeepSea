
{% set keyring_dir="/srv/salt/ceph/openattic/files/" %}
{% set keyring=keyring_dir + "ceph.client.openattic.keyring" %}

files dir:
  cmd.run:
    - name: "mkdir -p {{ keyring_dir }}"


openattic keyring:
  cmd.run:
    - name: "ceph-authtool -C -n client.openattic --gen-key {{ keyring }} --cap osd 'allow *' --cap mon 'allow *'"
    - unless: "stat {{ keyring }}" 

add auth:
  cmd.run:
    - name: "ceph auth add client.openattic -i {{ keyring }}"

permissions:
  cmd.run:
    - name: "chmod 644 {{ keyring }}"
