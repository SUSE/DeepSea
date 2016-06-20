

{# Include cluster assignment for each minion #}
{# Note: id doesn't work since the FQDN has a '.' #}

{# Second Note: admin node remains unassigned currently #}
{# 1) admin is an "unofficial" role allowing one admin node to manage
      any number of clusters #}
{# 2) admin is made an official role, but a host must then be able to 
      be part of two or more clusters #}
{# 3) I hope somebody has a better idea.  #}

include:
  - ceph.cluster.{{ grains['host'] }}

