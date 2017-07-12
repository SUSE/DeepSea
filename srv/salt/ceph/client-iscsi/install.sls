
open-iscsi:
  pkg.installed:
    - name: open-iscsi

iscsid:
  service.running:
    - name: iscsid
    - require:
      - pkg: open-iscsi
    
