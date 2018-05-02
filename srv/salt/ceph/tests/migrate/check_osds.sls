
#pillar:
#  cmd.run:
#    - name: echo "{{ pillar.get('ceph') }}"

check:
  osd.correct:
    - device: {{ salt['cmd.run']('cat /tmp/checklist') }}

