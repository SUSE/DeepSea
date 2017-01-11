class OutputHelper(object):
    def __init__(self, **kwargs):
        self.lsscsi_with_raid_fail = \
                 {'device': 'sdx',
                  'stdout': [
                  '[0:2:0:0]  disk    DELL     PERC H700 2.10  /dev/sda \n',
                  '[0:2:1:0]  disk    DELL     PERC H700 2.10  /dev/sdb \n',
                  '[0:2:2:0]  disk    DELL     PERC H700 2.10  /dev/sdc \n', 
                  '[0:2:3:0]  disk    DELL     PERC H700 2.10  /dev/sdd \n', 
                  '[0:2:4:0]  disk    DELL     PERC H700 2.10  /dev/sde \n', 
                  '[0:2:5:0]  disk    DELL     PERC H700 2.10  /dev/sdf \n', 
                  '[0:2:6:0]  disk    DELL     PERC H700 2.10  /dev/sdg \n', 
                  '[0:2:7:0]  disk    DELL     PERC H700 2.10  /dev/sdh \n', 
                  '[0:2:8:0]  disk    DELL     PERC H700  2.10  /dev/sdi \n', 
                  '[0:2:9:0]  disk    DELL     PERC H700  2.10  /dev/sdj \n', 
                  '[0:2:10:0] disk    DELL     PERC H700  2.10  /dev/sdk \n', 
                  '[0:2:11:0] disk    DELL     PERC H700  2.10  /dev/sdl \n', 
                  '[0:2:12:0] disk    DELL     PERC H700 2.10  /dev/sdm \n', 
                  '[0:2:13:0] disk    DELL     PERC H700  2.10  /dev/sdn \n',
                  '[1:0:0:0]  disk    iDRAC    LCDRIVE  0323  /dev/sdo \n', 
                  '[2:0:0:0]  cd/dvd  iDRAC    Virtual CD  0323  /dev/sr0 \n', 
                  '[2:0:0:1]  disk    iDRAC    Virtual Floppy 0323  /dev/sdp \n'],
                  'expected_return': None 
                 }

        self.lsscsi_with_raid_success = \
                 {'device': 'sda',
                  'stdout': [
                  '[0:2:0:0]  disk    DELL     PERC H700 2.10  /dev/sda \n',
                  '[0:2:1:0]  disk    DELL     PERC H700 2.10  /dev/sdb \n',
                  '[0:2:2:0]  disk    DELL     PERC H700 2.10  /dev/sdc \n', 
                  '[0:2:3:0]  disk    DELL     PERC H700 2.10  /dev/sdd \n', 
                  '[0:2:4:0]  disk    DELL     PERC H700 2.10  /dev/sde \n', 
                  '[0:2:5:0]  disk    DELL     PERC H700 2.10  /dev/sdf \n', 
                  '[0:2:6:0]  disk    DELL     PERC H700 2.10  /dev/sdg \n', 
                  '[0:2:7:0]  disk    DELL     PERC H700 2.10  /dev/sdh \n', 
                  '[0:2:8:0]  disk    DELL     PERC H700  2.10  /dev/sdi \n', 
                  '[0:2:9:0]  disk    DELL     PERC H700  2.10  /dev/sdj \n', 
                  '[0:2:10:0] disk    DELL     PERC H700  2.10  /dev/sdk \n', 
                  '[0:2:11:0] disk    DELL     PERC H700  2.10  /dev/sdl \n', 
                  '[0:2:12:0] disk    DELL     PERC H700 2.10  /dev/sdm \n', 
                  '[0:2:13:0] disk    DELL     PERC H700  2.10  /dev/sdn \n',
                  '[1:0:0:0]  disk    iDRAC    LCDRIVE  0323  /dev/sdo \n', 
                  '[2:0:0:0]  cd/dvd  iDRAC    Virtual CD  0323  /dev/sr0 \n', 
                  '[2:0:0:1]  disk    iDRAC    Virtual Floppy 0323  /dev/sdp \n'],
                  'expected_return': '0'
                 }

        self.lsscsi_with_raid_success_extra = \
                 {'device': 'sdg',
                  'stdout': [
                  '[0:2:0:0]  disk    DELL     PERC H700 2.10  /dev/sda \n',
                  '[0:2:1:0]  disk    DELL     PERC H700 2.10  /dev/sdb \n',
                  '[0:2:2:0]  disk    DELL     PERC H700 2.10  /dev/sdc \n', 
                  '[0:2:3:0]  disk    DELL     PERC H700 2.10  /dev/sdd \n', 
                  '[0:2:4:0]  disk    DELL     PERC H700 2.10  /dev/sde \n', 
                  '[0:2:5:0]  disk    DELL     PERC H700 2.10  /dev/sdf \n', 
                  '[0:2:6:0]  disk    DELL     PERC H700 2.10  /dev/sdg \n', 
                  '[0:2:7:0]  disk    DELL     PERC H700 2.10  /dev/sdh \n', 
                  '[0:2:8:0]  disk    DELL     PERC H700  2.10  /dev/sdi \n', 
                  '[0:2:9:0]  disk    DELL     PERC H700  2.10  /dev/sdj \n', 
                  '[0:2:10:0] disk    DELL     PERC H700  2.10  /dev/sdk \n', 
                  '[0:2:11:0] disk    DELL     PERC H700  2.10  /dev/sdl \n', 
                  '[0:2:12:0] disk    DELL     PERC H700 2.10  /dev/sdm \n', 
                  '[0:2:13:0] disk    DELL     PERC H700  2.10  /dev/sdn \n',
                  '[1:0:0:0]  disk    iDRAC    LCDRIVE  0323  /dev/sdo \n', 
                  '[2:0:0:0]  cd/dvd  iDRAC    Virtual CD  0323  /dev/sr0 \n', 
                  '[2:0:0:1]  disk    iDRAC    Virtual Floppy 0323  /dev/sdp \n'],
                  'expected_return': '7'
                 }
        self.sgdisk_valid_osd_data = \
                {'stdout': [
                  'Partition GUID code: 4FBD7E29-9D25-41B8-AFD0-062C0CEFF05D (Unknown)\n',
                  'Partition unique GUID: 083B45E3-6601-4239-8F9D-A0224A125A72\n', 
                  'First sector: 10487808 (at 5.0 GiB)\n', 
                  'Last sector: 3905945566 (at 1.8 TiB)\n', 
                  'Partition size: 3895457759 sectors (1.8 TiB)\n', 
                  'Attribute flags: 0000000000000000\n', 
                  "Partition name: 'ceph data'\n"],
                 'expected_return': True
                }

        self.sgdisk_valid_journal = \
                {'stdout': [
                    'Partition GUID code: 45B0969E-9B03-4F30-B4C6-B4B80CEFF106 (Unknown)\n',
                    'Partition unique GUID: 4C91DA56-DBF5-49CA-8B75-454AB0FE17A2\n', 
                    'First sector: 2048 (at 1024.0 KiB)\n', 
                    'Last sector: 10487807 (at 5.0 GiB)\n', 
                    'Partition size: 10485760 sectors (5.0 GiB)\n', 
                    'Attribute flags: 0000000000000000\n', 
                    "Partition name: 'ceph journal'\n"],
                  'expected_return': True
                 }

        self.sgdisk_invalid = \
                {'stdout': [
                    'Partition GUID code: 21686148-6449-6E6F-744E-656564454649 (BIOS boot partition)\n',
                    'Partition unique GUID: 663F930C-7BE2-4803-8C03-83A93E285C95\n', 
                    'First sector: 2048 (at 1024.0 KiB)\n', 
                    'Last sector: 1060863 (at 518.0 MiB)\n', 
                    'Partition size: 1058816 sectors (517.0 MiB)\n', 
                    'Attribute flags: 0000000000000000\n', 
                    "Partition name: 'primary'\n"],
                   'expected_return': False
                }

        self.hwinfo = \
                {'stdout': [
                   '33: SCSI 20.0: 10600 Disk\n', 
                   '  [Created at block.245]\n', 
                   '  Unique ID: R7kM.9VTsoSFJ_MD\n', 
                   '  Parent ID: B35A.z2vxpHnh8UC\n', 
                   '  SysFS ID: /class/block/sda\n', 
                   '  SysFS BusID: 0:2:0:0\n', 
                   '  SysFS Device Link: /devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:0/0:2:0:0\n', 
                   '  Hardware Class: disk\n', 
                   '  Model: "DELL PERC H700"\n', 
                   '  Vendor: "DELL"\n', 
                   '  Device: "PERC H700"\n', 
                   '  Revision: "2.10"\n', 
                   '  Serial ID: "00fc74e006176c3d1b00ef6ace20a782"\n', 
                   '  Driver: "megaraid_sas", "sd"\n', 
                   '  Driver Modules: "megaraid_sas", "sd_mod"\n', 
                   '  Device File: /dev/sda (/dev/sg0)\n', 
                   '  Device Files: /dev/sda, /dev/disk/by-id/scsi-36b82a720ce6aef001b3d6c1706e074fc, /dev/disk/by-id/scsi-SDELL_PERC_H700_00fc74e006176c3d1b00ef6ace20a782, /dev/disk/by-id/wwn-0x6b82a720ce6aef001b3d6c1706e074fc, /dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:0:0\n', 
                   '  Device Number: block 8:0-8:15 (char 21:0)\n', 
                   '  Geometry (Logical): CHS 243133/255/63\n', 
                   '  Size: 3905945600 sectors a 512 bytes\n', 
                   '  Capacity: 1862 GB (1999844147200 bytes)\n', 
                   '  Config Status: cfg=no, avail=yes, need=no, active=unknown\n', 
                   '  Attached to: #29 (RAID bus controller)\n'],

                 'expected_return':

                    {'Attached to': '#29 (RAID bus controller)',
                     'Bytes': '1999844147200',
                     'Capacity': '1862 GB',
                     'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
                     'Device': 'PERC H700',
                     'Device File': '/dev/sda',
                     'Device Files': '/dev/sda, /dev/disk/by-id/scsi-36b82a720ce6aef001b3d6c1706e074fc, /dev/disk/by-id/scsi-SDELL_PERC_H700_00fc74e006176c3d1b00ef6ace20a782, /dev/disk/by-id/wwn-0x6b82a720ce6aef001b3d6c1706e074fc, /dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:0:0',
                     'Device Number': 'block 8:0-8:15 (char 21:0)',
                     'Driver': 'megaraid_sas, sd',
                     'Driver Modules': 'megaraid_sas, sd_mod',
                     'Geometry (Logical)': 'CHS 243133/255/63',
                     'Hardware Class': 'disk',
                     'Model': 'DELL PERC H700',
                     'Parent ID': 'B35A.z2vxpHnh8UC',
                     'Revision': '2.10',
                     'Serial ID': '00fc74e006176c3d1b00ef6ace20a782',
                     'Size': '3905945600 sectors a 512 bytes',
                     'SysFS BusID': '0:2:0:0',
                     'SysFS Device Link': '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:0/0:2:0:0',
                     'SysFS ID': '/class/block/sda',
                     'Unique ID': 'R7kM.9VTsoSFJ_MD',
                     'Vendor': 'DELL'
                    },
                'function_args': 'sda'

                   }
        self.smartctl_spinner_valid= \
               { 'stdout':[
                     'smartctl 6.2 2013-11-07 r3856 [x86_64-linux-4.4.21-90-default] (SUSE RPM)\n',
                     'Copyright (C) 2002-13, Bruce Allen, Christian Franke, www.smartmontools.org\n',
                     '\n',
                     '=== START OF INFORMATION SECTION ===\n',
                     'Vendor:               SEAGATE\n',
                     'Product:              ST2000NM0023\n',
                     'Revision:             GS0D\n',
                     'User Capacity:        2,000,398,934,016 bytes [2.00 TB]\n',
                     'Logical block size:   512 bytes\n',
                     'Logical block provisioning type unreported, LBPME=-1, LBPRZ=0\n',
                     'Rotation Rate:        7200 rpm\n',
                     'Form Factor:          3.5 inches\n',
                     'Logical Unit id:      0x5000c50058848a77\n',
                     'Serial number:        Z1X28E90\n',
                     'Device type:          disk\n',
                     'Transport protocol:   SAS\n',
                     'Local Time is:        Wed Jan 25 14:43:46 2017 CET\n',
                     'SMART support is:     Available - device has SMART capability.\n',
                     'SMART support is:     Enabled\n',
                     'Temperature Warning:  Disabled or Not Supported\n',
                     '\n'],
                    'expected_return': '1'
                }
        self.smartctl_solid_state_valid = \
                { 'stdout': [
                     'smartctl 6.2 2013-11-07 r3856 [x86_64-linux-4.4.21-90-default] (SUSE RPM)\n',
                     'Copyright (C) 2002-13, Bruce Allen, Christian Franke, www.smartmontools.org\n',
                     '\n',
                     '=== START OF INFORMATION SECTION ===\n',
                     'Vendor:               Pliant\n',
                     'Product:              LB206S\n',
                     'Revision:             D323\n',
                     'User Capacity:        200,049,647,616 bytes [200 GB]\n',
                     'Logical block size:   512 bytes\n',
                     'LU is resource provisioned, LBPRZ=1\n',
                     'Rotation Rate:        Solid State Device\n',
                     'Form Factor:          2.5 inches\n',
                     'Logical Unit id:      0x5001e820027786fc\n',
                     'Serial number:        41387772\n',
                     'Device type:          disk\n',
                     'Transport protocol:   SAS\n',
                     'Local Time is:        Wed Jan 25 14:47:19 2017 CET\n',
                     'SMART support is:     Available - device has SMART capability.\n',
                     'SMART support is:     Enabled\n',
                     'Temperature Warning:  Disabled or Not Supported\n',
                     '\n'],
                    'expected_return': '0'
                      
                }
        self.smartctl_invalid = \
                    { 'stdout': [
                         'smartctl 6.2 2013-11-07 r3856 [x86_64-linux-4.4.21-90-default] (SUSE RPM)\n',
                         'Copyright (C) 2002-13, Bruce Allen, Christian Franke, www.smartmontools.org\n',
                         '\n',
                         "/dev/sda: Unknown device type 'asd,0'\n",
                         '=======> VALID ARGUMENTS ARE: ata, scsi, sat[,auto][,N][+TYPE], usbcypress[,X], usbjmicron[,p][,x][,N], usbsunplus, marvell, areca,N/E, 3ware,N, hpt,L/M/N, megaraid,N, cciss,N, auto, test <=======\n',
                         '\n', 'Use smartctl -h to get a usage summary\n',
                         '\n'],
                     'expected_return': '1'
                    }
        self.lspci_out_hwraid_megaraid= \
                { 'stdout': [
                    '02:00.0 RAID bus controller: LSI Logic / Symbios Logic MegaRAID SAS 2108 [Liberator] (rev 05)\n', 
                    '\tKernel driver in use: megaraid_sas\n', 
                    '\tKernel modules: megaraid_sas\n'],
                  'controller_name': 'megaraid',
                  'raidtype': 'hardware'
                }

        self.lspci_out_hwraid_aacraid = \
                { 'stdout': [
                    '02:00.0 RAID bus controller: Adaptec AAC-RAID ![9005:0285] (rev 01) \n', 
                    '\tKernel driver in use: aacraid\n', 
                    '\tKernel modules: aacraid\n'],
                  'controller_name': 'aacraid',
                  'raidtype': 'hardware'
                }

        self.lspci_out_hwraid_cciss = \
                { 'stdout': [
                    # incomplete 
                    '\tKernel driver in use: cciss\n', 
                    '\tKernel modules: hpsa, cciss\n'],
                  'controller_name': 'cciss',
                  'raidtype': 'hardware'
                }

        self.lspci_out_hwraid_areca = \
                { 'stdout': [
                    'RAID bus controller: Areca Technology Corp. ARC-1680 8 port PCIe/PCI-X to SAS/SATA II RAID Controller\n',
                    '\tKernel driver in use: arcmsr\n', 
                    '\tKernel modules: arcmsr\n'],
                  'controller_name': 'areca',
                  'raidtype': 'hardware'
                }

        self.lspci_out_hwraid_3ware = \
                { 'stdout': [
                    '08:00.0 RAID bus controller [0104]: 3ware Inc 9690SA SAS/SATA-II RAID PCIe [13c1:1005] (rev 01)\n',
                    '\tKernel driver in use: 3w\n', 
                    '\tKernel modules: 3w\n'],
                  'controller_name': '3ware',
                  'raidtype': 'hardware'
                }

        self.lshw_out = \
                { 'stdout': '<?xml version="1.0" standalone="yes" ?>\n<!-- generated by lshw-unknown -->\n<!-- GCC 4.8.5 -->\n<!-- Linux 4.1.34-33-default #1 SMP PREEMPT Thu Oct 20 08:03:29 UTC 2016 (fe18aba) x86_64 -->\n<!-- GNU libc 2 (glibc 2.19) -->\n<list>\n  <node id="disk" claimed="true" class="disk" handle="SCSI:00:00:00:00">\n   <description>ATA Disk</description>\n   <product>ST500DM002-1BD14</product>\n   <vendor>Seagate</vendor>\n   <physid>0.0.0</physid>\n   <businfo>scsi@0:0.0.0</businfo>\n   <logicalname>/dev/sda</logicalname>\n   <dev>8:0</dev>\n   <version>KC47</version>\n   <serial>Z6E0K57T</serial>\n   <size units="bytes">500107862016</size>\n   <configuration>\n    <setting id="ansiversion" value="5" />\n    <setting id="logicalsectorsize" value="512" />\n    <setting id="sectorsize" value="4096" />\n    <setting id="signature" value="2bd2c32a" />\n   </configuration>\n   <capabilities>\n    <capability id="partitioned" >Partitioned disk</capability>\n    <capability id="partitioned:dos" >MS-DOS partition table</capability>\n   </capabilities>\n  </node>\n  <node id="disk" claimed="true" class="disk" handle="SCSI:01:00:00:00">\n   <description>ATA Disk</description>\n   <product>Samsung SSD 850</product>\n   <physid>0.0.0</physid>\n   <businfo>scsi@1:0.0.0</businfo>\n   <logicalname>/dev/sdb</logicalname>\n   <logicalname>/home/jxs/images</logicalname>\n   <dev>8:16</dev>\n   <version>2B6Q</version>\n   <serial>S251NXAH235352J</serial>\n   <size units="bytes">256060514304</size>\n   <configuration>\n    <setting id="ansiversion" value="5" />\n    <setting id="logicalsectorsize" value="512" />\n    <setting id="mount.fstype" value="xfs" />\n    <setting id="mount.options" value="rw,relatime,attr2,inode64,noquota" />\n    <setting id="sectorsize" value="512" />\n    <setting id="state" value="mounted" />\n   </configuration>\n  </node>\n  <node id="cdrom" claimed="true" class="disk" handle="SCSI:02:00:00:00">\n   <description>DVD-RAM writer</description>\n   <product>DVD+-RW GHB0N</product>\n   <vendor>HL-DT-ST</vendor>\n   <physid>0.0.0</physid>\n   <businfo>scsi@2:0.0.0</businfo>\n   <logicalname>/dev/cdrom</logicalname>\n   <logicalname>/dev/cdrw</logicalname>\n   <logicalname>/dev/dvd</logicalname>\n   <logicalname>/dev/dvdrw</logicalname>\n   <logicalname>/dev/sr0</logicalname>\n   <dev>11:0</dev>\n   <version>A100</version>\n   <configuration>\n    <setting id="ansiversion" value="5" />\n    <setting id="status" value="nodisc" />\n   </configuration>\n   <capabilities>\n    <capability id="removable" >support is removable</capability>\n    <capability id="audio" >Audio CD playback</capability>\n    <capability id="cd-r" >CD-R burning</capability>\n    <capability id="cd-rw" >CD-RW burning</capability>\n    <capability id="dvd" >DVD playback</capability>\n    <capability id="dvd-r" >DVD-R burning</capability>\n    <capability id="dvd-ram" >DVD-RAM burning</capability>\n   </capabilities>\n  </node>\n</list>\n',
                  'expected_return': 
                  
                  {'/dev/sdb': 
                    {'Model': 'Samsung SSD 850', 
                     'Device File': 'mocked_udevadm_out',
                     'Capacity': 256, 
                     'Serial ID': 
                     'S251NXAH235352J'}, 

                   '/dev/sda': 
                    {'Model': 'ST500DM002-1BD14', 
                     'Device File': 'mocked_udevadm_out', 
                     'Capacity': 500,
                     'Serial ID': 'Z6E0K57T'},
                  }
                }
        self._udevadm_out = \
                { 'stdout':
                        'P: /devices/pci0000:00/0000:00:1f.2/ata1/host0/target0:0:0/0:0:0:0/block/sda\nN: sda\nS: disk/by-id/ata-ST500DM002-1BD142_Z6E0K57T\nS: disk/by-id/scsi-0ATA_ST500DM002-1BD14_Z6E0K57T\nS: disk/by-id/scsi-1ATA_ST500DM002-1BD142_Z6E0K57T\nS: disk/by-id/scsi-35000c5006642f522\nS: disk/by-id/scsi-SATA_ST500DM002-1BD14_Z6E0K57T\nS: disk/by-id/scsi-SATA_ST500DM002-1BD1_Z6E0K57T\nS: disk/by-id/wwn-0x5000c5006642f522\nS: disk/by-path/pci-0000:00:1f.2-ata-1.0\nS: disk/by-path/pci-0000:00:1f.2-scsi-0:0:0:0\nE: DEVLINKS=/dev/disk/by-id/ata-ST500DM002-1BD142_Z6E0K57T /dev/disk/by-id/scsi-0ATA_ST500DM002-1BD14_Z6E0K57T /dev/disk/by-id/scsi-1ATA_ST500DM002-1BD142_Z6E0K57T /dev/disk/by-id/scsi-35000c5006642f522 /dev/disk/by-id/scsi-SATA_ST500DM002-1BD14_Z6E0K57T /dev/disk/by-id/scsi-SATA_ST500DM002-1BD1_Z6E0K57T /dev/disk/by-id/wwn-0x5000c5006642f522 /dev/disk/by-path/pci-0000:00:1f.2-ata-1.0 /dev/disk/by-path/pci-0000:00:1f.2-scsi-0:0:0:0\nE: DEVNAME=/dev/sda\nE: DEVPATH=/devices/pci0000:00/0000:00:1f.2/ata1/host0/target0:0:0/0:0:0:0/block/sda\nE: DEVTYPE=disk\nE: ID_ATA=1\nE: ID_BUS=ata\nE: ID_MODEL=ST500DM002-1BD14\nE: ID_MODEL_ENC=ST500DM002-1BD14\nE: ID_PART_TABLE_TYPE=dos\nE: ID_PART_TABLE_UUID=2bd2c32a\nE: ID_PATH=pci-0000:00:1f.2-ata-1.0\nE: ID_PATH_COMPAT=pci-0000:00:1f.2-scsi-0:0:0:0\nE: ID_PATH_TAG=pci-0000_00_1f_2-ata-1_0\nE: ID_REVISION=KC47\nE: ID_SCSI=1\nE: ID_SCSI_COMPAT=SATA_ST500DM002-1BD14_Z6E0K57T\nE: ID_SCSI_COMPAT_TRUNCATED=SATA_ST500DM002-1BD1_Z6E0K57T\nE: ID_SCSI_DI=1\nE: ID_SCSI_SN=1\nE: ID_SERIAL=ST500DM002-1BD142_Z6E0K57T\nE: ID_SERIAL_SHORT=Z6E0K57T\nE: ID_TYPE=disk\nE: ID_VENDOR=ATA\nE: ID_VENDOR_ENC=ATA\\x20\\x20\\x20\\x20\\x20\nE: ID_WWN=0x5000c5006642f522\nE: ID_WWN_WITH_EXTENSION=0x5000c5006642f522\nE: MAJOR=8\nE: MINOR=0\nE: MPATH_SBIN_PATH=/sbin\nE: SCSI_IDENT_LUN_ATA=ST500DM002-1BD142_Z6E0K57T\nE: SCSI_IDENT_LUN_NAA_REG=5000c5006642f522\nE: SCSI_IDENT_LUN_T10=ATA_ST500DM002-1BD142_Z6E0K57T\nE: SCSI_IDENT_LUN_VENDOR=Z6E0K57T\nE: SCSI_IDENT_SERIAL=Z6E0K57T\nE: SCSI_MODEL=ST500DM002-1BD14\nE: SCSI_MODEL_ENC=ST500DM002-1BD14\nE: SCSI_REVISION=KC47\nE: SCSI_TPGS=0\nE: SCSI_TYPE=disk\nE: SCSI_VENDOR=ATA\nE: SCSI_VENDOR_ENC=ATA\\x20\\x20\\x20\\x20\\x20\nE: SUBSYSTEM=block\nE: TAGS=:systemd:\nE: USEC_INITIALIZED=404784\n\n',
                        'expected_return': '/dev/sda'
                }

