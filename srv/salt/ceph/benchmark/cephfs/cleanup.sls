unmount cephfs:
  mount.unmounted:
    - name: {{ salt['pillar.get']('benchmark:base-directory')}}
