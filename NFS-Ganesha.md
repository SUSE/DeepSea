### NFS-Ganesha ###
[NFS-Ganesha](https://github.com/nfs-ganesha/nfs-ganesha/) is a user-mode file server for NFS. It supports various File System Abstraction Layers (FSAL). Deepsea supports deployment of NFS-Ganesha for Ceph and RGW FSAL. 

### Prerequisite ###
* NFS-Ganesha version 2.5-dev7 or higher.
* An active mds or rgw in ceph cluster.
  
### Available Role ###
Deepsea provides a default “ganesha” role.
It's possible to create your own [custom roles](#custom-roles) for more flexibility.

### Configuration file ###
NFS-Ganesha requires a 
[configuration file](https://github.com/nfs-ganesha/nfs-ganesha/wiki/ConDeploying figurationfile/).
Deepsea provides a default ganesha configuration file, /srv/salt/ceph/ganesha/files/ganesha.conf.j2. 
This supports both Ceph and RGW FSAL. The conf file is populated with proper ganesha keyrings at deployment time. 
Users can either modify the given ganesha.conf.j2 file or add {{[custom_role](#custom-roles)}}.conf.j2 file. 

### Keyrings ###
NFS-Ganesha requires proper keyring to authenticate with libcephfs and librgw. 
The default ganesha keyring file is present at /srv/salt/ceph/ganesha/files/ganesha.j2.
Users can either modify existing keyring or add {{[custom_role](#custom-roles)}}.j2. 

### Ganesha + RGW FSAL ###
NFS-Ganesha RGW FSAL requires S3 user id, access key and secret access key. 
It can be provided in the file /srv/pillar/ceph/rgw.sls. 
Refer to example file: /srv/pillar/ceph/rgw.sls.example. 

### Custom roles ###
To create a custom ganesha role (e.g. silver)
* Define ganesha_configurations in rgw.sls

    ``` 
     ganesha_configurations:

      - silver
     ```
* Add file, silver.conf.j2 and silver.j2 under /srv/salt/ceph/ganesha/files.
* If you want to use this custom role "silver" with rgw configurations, define
   
   ``` 
   rgw_configurations:
     silver:
      users:
      - { uid: "demo", name: "Demo", email: "demo@demo.nil" }
    ``` 

### Deploying Ganesha server ##
1. After stage 1, assign ganesha or custom roles in /srv/pillar/ceph/proposal/policy.cfg
2. In case of custom roles, provide the correct config and keyring file. 
2. Run stage 2-4. Ganesha is run as part of stage 4.  

### Examples ###
* Ganesha role with both Ceph and RGW on same node.
  - Assign roles: ganesha, rgw and mds to nodes in cluster. 
  - Define [rgw users](#custom-roles)
  - Run the stages upto 4. 
  You should see ganesha server running on single node with both FSALs.
  
* NFS-Ganesha server with CephFS and RGW on different nodes
  - Assign custom roles, ganesha_cephfs and ganesha_rgw to nodes. 
  - Add new conf file, ganesha_cephfs.conf.j2 and ganesha_rgw.conf.j2,
    with their respective FSALs.
  - Add keyring file, ganesha_cephfs.j2 and ganesha_rgw.j2 
  - Update rgw.sls to reflect new ganesha_configuraitons and rgw_configurations  
  - Run the stages upto 4
  
  You should see two different ganesha servers running on different nodes. 

* Custom RGW and Ganesha roles 
  In case you want to run ganesha server for different users on different nodes,
  you can define custom ganesha roles and respective rgw roles. Rgw configurations
  can contain different set of users
   ``` 
     rgw_configurations:

      - silver 

        users:

         - { uid: "demo", name: "Demo", email: "demo@demo.nil" }


      - gold

        users:

         - { uid: "demo1", name: "Demo1", email: "demo1@demo.nil" }

     ```
   
     ``` 
     ganesha_configurations:

      - silver
 
      - gold 
     ```

### Debugging ###
NFS-Ganesha service is started with log file, /etc/sysconfig/ganesha.
The log files are written at /var/log/ganesha.log. 
By default the log level is set to "NIV_CRIT". 
In case more verbosity is required, NIV_DEBUG and NIV_FULL_DEBUG can be used.