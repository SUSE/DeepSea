
install jq:
  pkg.installed:
    - pkgs:
      - jq
    - refresh: True

check config:
  cmd.run:
    - name: "ceph --admin-daemon /var/run/ceph/ceph-mon.*.asok config get mon_pg_warn_min_per_osd | jq '.mon_pg_warn_min_per_osd' | grep -q 16"

