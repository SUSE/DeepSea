'use strict';

/*
 * LRBD Utilities.
 */

/*******************************************************************************
 * LRBD Target
 ******************************************************************************/

/* An LRBD target host entry.
 * host = { "host": String, "portal": String }
 */
class LRBDTargetHost {
    constructor(host, portal) {
        this.host = host;
        this.portal = portal;
    }
}

/* An LRBD target entry.
 * target = { "hosts": [host:obj], "target": String }
 * It's possible that custom key:value entries will be added to the target.
 * TODO: should an undefined targetName generate an error?
 */
class LRBDTarget {
    constructor(targetName, hosts) {
        this.target = targetName ? targetName : "undefined";
        this.hosts = hosts ? hosts : [];
    }
}

/*******************************************************************************
 * LRBD Portal
 ******************************************************************************/

/* An LRBD portal entry.
 * portal = { "name": String, "addresses": [String] }
 * TODO: should an undefined name generate an error?
 */
class LRBDPortal {
    constructor(name, addresses) {
        this.name = name ? name : "undefined";
        this.addresses = addresses ? addresses : [];
    }
}

/*******************************************************************************
 * LRBD Auth
 ******************************************************************************/

/* The most basic tpg entry consisting of a userid and password. */
class LRBDAuthTPG {
    constructor(userid, password) {
        this.userid = userid;
        this.password = password;
    }
}

/* tpg (userid and password) + mutual auth related credentials. */
class LRBDAuthTPGMutual extends LRBDAuthTPG {
    constructor(userid, password, mutual, userid_mutual, password_mutual) {
        super(userid, password);
        this.mutual = mutual === "enable" ? mutual : "disable";
        this.userid_mutual = userid_mutual;
        this.password_mutual = password_mutual;
    }
}

/* discovery section for which we extend LRBDAuthTPG out of convenience. */
class LRBDAuthDiscovery extends LRBDAuthTPG {
    constructor(userid, password, auth) {
        super(userid, password);
        this.auth = auth === "enable" ? auth : "disable";
    }
}

/* discovery + mutual auth related credentials.
 * Note that this duplicates a bit of code (ie. from LRBDAuthTPGMutual),
 * however I've not yet tried to create a parent that extends two subclasses
 * with proper prototype combining (TODO):
 * (http://stackoverflow.com/questions/29879267/es6-class-multiple-inheritance).
 */
class LRBDAuthDiscoveryMutual extends LRBDAuthDiscovery {
    constructor(userid, password, auth, mutual, userid_mutual, password_mutual) {
        super(userid, password, auth);
        this.mutual = mutual === "enable" ? mutual : "disable";
        this.userid_mutual = userid_mutual;
        this.password_mutual = password_mutual;
    }
}

/* An LRBD Auth entry.
 */
class LRBDAuth {
    constructor(authentication, target, tpg, discovery) {
        this.authentication = authentication;
        this.target = target ? target : "undefined";
        /* tpg and discovery are optional. */
        if (tpg) {
            this.tpg = tpg;
        }
        if (discovery) {
            this.discovery = discovery;
        }
    }
}
LRBDAuth.supportedTypes = ["none", "tpg", "tpg+identified"];

/*******************************************************************************
 * LRBD Pools
 ******************************************************************************/

class LRBDPoolGatewayTPG {
    constructor(portal, initiator, image) {
        this.portal = portal;
        this.initiator = initiator;
        this.image = image;
    }
}

/* LRBD Pool Gateway entry.
 * { "host": String, "tpg": [ {LRBDPoolGatewayTPG}, ... ] }
 */
class LRBDPoolGateway {
    constructor(host, tpg) {
        this.host = host;
        this.tpg = tpg ? tpg : [];
    }
}

/* LRBD Pool entry.
 * { "pool": String, "gateways": [ {LRBDPoolGateway}, ... ] }
 */
class LRBDPool {
    constructor(pool, gateways) {
        this.pool = pool;
        this.gateways = gateways ? gateways : [];
    }
}

/* An LRBD Configuration composed of:
 *  {
 *    "auth":    [ {LRBDAuth},   ... ],
 *    "targets": [ {LRBDTarget}, ... ],
 *    "portals": [ {LRBDPortal}, ... ],
 *    "pools":   [ {LRBDPool},   ... ],
 *  }
 */
class LRBDConf {
    constructor() {
        this.setAllEmpty();
    }

    setAllEmpty() {
        this.auth = [];
        this.targets = [];
        this.portals = [];
        this.pools = [];
    }

    /**************************************************************************
     * LRBDConf population from an lrbd.conf file object.
     *************************************************************************/

    /* Helper method to populate this.auth.  Returns true/false. */
    _populateAuthFromFile(authArr) {
        console.log("_populateAuthFromFile()");

        /* A null authArr signals that the lrbd.conf is missing this
         * section and thus is incomplete.  Fail here.
         */
        if (!authArr) {
            return false;
        }

        for (var i = 0; i < authArr.length; i++) {
            var auth = authArr[i];

            /* Check to make sure it has the minimal set of keys need and a supported
             * authentication type.
             */
            if (!auth.hasOwnProperty('authentication') || !auth.hasOwnProperty('target') ||
                LRBDAuth.supportedTypes.indexOf(auth.authentication) == -1) {
                return false;
            }

            /* Barebones LRBDAuth entry. */
            var lrbdAuth = new LRBDAuth(auth.authentication, auth.target, null, null);

            /* Check for tpg.  tpg can also have a mutual section. */
            if (auth.tpg) {
                var tpgObj;
                if (auth.tpg.mutual) {
                    tpgObj = new LRBDAuthTPGMutual(auth.tpg.userid, auth.tpg.password,
                                                   auth.tpg.mutual, auth.tpg.userid_mutual,
                                                   auth.tpg.password_mutual);
                } else {
                    tpgObj = new LRBDAuthTPG(auth.tpg.userid, auth.tpg.password);
                }

                /* Attach our tpgObj. */
                lrbdAuth.tpg = tpgObj;
            }

            /* Finally check for discovery */
            if (auth.discovery) {
                var disc;
                if (auth.discovery.mutual) {
                    disc = new LRBDAuthDiscoveryMutual(auth.discovery.userid, auth.discovery.password,
                                                       auth.discovery.auth, auth.discovery.mutual,
                                                       auth.discovery.userid_mutual, auth.discovery.password_mutual);

                } else {
                    disc = new LRBDAuthDiscovery(auth.discovery.userid, auth.discovery.password,
                                                 auth.discovery.auth);
                }

                /* Attach discovery. */
                lrbdAuth.discovery = disc;
            }

            /* Add our auth entry. */
            this.auth.push(lrbdAuth);
        }

        return true;
    }

    /* Helper method to populate this.targets.  Returns true/false. */
    _populateTargetsFromFile(targetsArr) {
        console.log("_populateTargetsFromFile()");

        /* Validate the format of the targets section.  If no targets are specified,
         * return a failure immediately.
         */
        if (!targetsArr || !targetsArr.length) {
            return false;
        }

        for (var i = 0; i < targetsArr.length; i++) {
            var target = targetsArr[i];

            /* Make sure the keys we care about are present, otherwise the target is
             * of an unsupported form.  Later we compile custom key:val's as well.
             */
            if (!target.hasOwnProperty('hosts') || !target.hasOwnProperty('target')) {
                return false;
            }

            /* Instantiate a new LRBDTarget.  Leave hosts array empty for now. */
            var lrbdTarget = new LRBDTarget(target.target, null);

            /* Now, examine the target.hosts array, and instantiage LRBDTargetHosts accordingly. */
            for (var j = 0; j < target.hosts.length; j++) {
                var targetHost = target.hosts[j];
                /* Make sure targetHost is of the the correct format. */
                if (Object.keys(targetHost).length != 2 ||
                    !targetHost.hasOwnProperty('host') || !targetHost.hasOwnProperty('portal')) {
                    return false;
                }

                /* Instantiate an LRBDTargetHost from targetHost and push to our LRBDTarget. */
                lrbdTarget.hosts.push(new LRBDTargetHost(targetHost.host, targetHost.portal));
            }

            /* It's possible for the target configuration to hold custom key:value pairs.
             * Include them as custom properties.
             */
            for (var k in target) {
                if (k != 'hosts' && k != 'target') {
                    lrbdTarget[k] = target[k];
                }
            }

            /* Finally, push the lrbdTarget to this.targets. */
            this.targets.push(lrbdTarget);
        }

        return true;
    }

    /* Helper method to populate this.portals.  Returns true/false. */
    _populatePortalsFromFile(portalsArr) {
        console.log("_populatePortalsFromFile()");

        /* A null portalsArr signals that the lrbd.conf is missing this
         * section and thus is incomplete.  Fail here.
         */
        if (!portalsArr) {
            return false;
        }

        /* We allow the case where the portals entry is empty.  This would
         * indicate that the user simply has not added any nodes to any
         * target entries.
         */
        for (var i = 0; i < portalsArr.length; i++) {
            var portal = portalsArr[i];

            /* Ensure portal is of the expected form. */
            if (Object.keys(portal).length != 2 || !portal.hasOwnProperty('name') ||
                !portal.hasOwnProperty('addresses')) {
                return false;
            }

            /* Now, examine the portal.address array.  Make sure each entry is a string. */
            for (var j = 0; j < portal.addresses.length; j++) {
                if (typeof(portal.addresses[j]) !== 'string') {
                    return false;
                }
            }

            /* If we're still here, go ahead and instantiate a new LRBDPortal. */
            var lrbdPortal = new LRBDPortal(portal.name, portal.addresses);

            /* Finally, push the lrbdPortal to this.portals. */
            this.portals.push(lrbdPortal);
        }

        return true;
    }

    /* Helper method to populate this.pools.  Returns true/false. */
    _populatePoolsFromFile(poolsArr) {
        console.log("_populatePoolsFromFile()");

        /* A null poolsArr signals that the lrbd.conf is missing this
         * section and thus is incomplete.  Fail here.
         */
        if (!poolsArr) {
            return false;
        }

        for (var i = 0; i < poolsArr.length; i++) {
            var pool = poolsArr[i];

            /* Create an LRBDPool with an empty gateways array. */
            var lrbdPool = new LRBDPool(pool.pool, null);

            for (var j = 0; j < pool.gateways.length; j++) {
                var poolGateway = pool.gateways[j];

                var lrbdPoolGateway = new LRBDPoolGateway(poolGateway.host, null);

                for (var k = 0; k < poolGateway.tpg.length; k++) {
                    var poolGatewayTPG = poolGateway.tpg[k];

                    var lrbdPoolGatewayTPG = new LRBDPoolGatewayTPG(poolGatewayTPG.portal,
                                                                    poolGatewayTPG.initiator,
                                                                    poolGatewayTPG.image);
                    lrbdPoolGateway.tpg.push(lrbdPoolGatewayTPG);
                }

                lrbdPool.gateways.push(lrbdPoolGateway);
            }

            this.pools.push(lrbdPool);
        }

        return true;
    }

    /* Takes a JSON representation of an lrbd.conf and populates
     * itself.  Returns true on success, false on failure.
     * TODO: Should a final cross check be made to ensure sanity across all sections?
     *       ie. entries in portals should align with portal entries in targets.
     */
    populateFromFile(fileObj) {
        var ret = true;

        /* Before every populate attempt, clear out the current data. */
        this.setAllEmpty();

        console.log("Populating LRBDConf from file: " + JSON.stringify(fileObj));

        if (!fileObj) {
            console.error("Null lrbd file object.");
            return false;
        }

        /* If we fail to populate this.targets, it doesn't make sense to
         * parse other sections, as they are all tied to an iSCSI target.
         */
        if (!this._populateTargetsFromFile(fileObj.targets)) {
            console.error("Failed to parse 'targets' section of LRBD configuration. ");
            ret = false;
        } else {
            if (!this._populateAuthFromFile(fileObj.auth)) {
                ret = false;
                console.error("Failed to parse 'auth' section of LRBD configuration. ");
            }
            if (!this._populatePortalsFromFile(fileObj.portals)) {
                ret = false;
                console.error("Failed to parse 'portals' section of LRBD configuration. ");
            }
            if (!this._populatePoolsFromFile(fileObj.pools)) {
                ret = false;
                console.error("Failed to parse 'pools' section of LRBD configuration. ");
            }
        }

        if (!ret) {
            console.error("Failed to parse one or more LRBD configuration sections.  Clearing.");
            this.setAllEmpty();
        }

        return ret;
    }


    /**************************************************************************
     * LRBDConf population from the UI.
     *************************************************************************/

    /* Helper method to poulate this.auth. Returns true/false. */
    _populateAuthFromUI(uiTargetsArr) {
        console.log("_populateAuthFromUI()");

        for (var i = 0; i < uiTargetsArr.length; i++) {
            var uiTarget = uiTargetsArr[i];
            var uiTargetAuth = uiTarget.auth;
            var lrbdAuth;

            /* Create our barebones LRBDAuth. */
            if (!uiTargetAuth) {
                /* No auth configured. */
                lrbdAuth = new LRBDAuth("none", uiTarget.name, null, null);
            } else {
                var tpgObj;

                /* Determine common auth type. */
                if (!uiTargetAuth.initiatorList.length) {
                    lrbdAuth = new LRBDAuth("tpg", uiTarget.name, null, null);
                } else {
                    lrbdAuth = new LRBDAuth("tpg+identified", uiTarget.name, null, null);
                }

                /* Check for mutual auth before determining tpg. */
                if (uiTargetAuth.mutualAuth) {
                    var mutEnabled = uiTargetAuth.mutualAuth.enabled ? "enable" : "disable";
                    tpgObj = new LRBDAuthTPGMutual(uiTargetAuth.userid, uiTargetAuth.password,
                                                   mutEnabled, uiTargetAuth.mutualAuth.userid,
                                                   uiTargetAuth.mutualAuth.password);
                } else {
                    tpgObj = new LRBDAuthTPG(uiTargetAuth.userid, uiTargetAuth.password);
                }

                /* Finally check for discovey auth. */
                if (uiTargetAuth.discoveryAuth) {
                    var discObj;
                    var discEnabled = uiTargetAuth.discoveryAuth.enabled ? "enable" : "disable";

                    if (uiTargetAuth.discoveryAuth.mutualAuth) {
                        var discMutEnabled = uiTargetAuth.discoveryAuth.mutualAuth.enabled ? "enable" : "disable";
                        discObj = new LRBDAuthDiscoveryMutual(uiTargetAuth.discoveryAuth.userid,
                                                              uiTargetAuth.discoveryAuth.password,
                                                              discEnabled, discMutEnabled,
                                                              uiTargetAuth.discoveryAuth.mutualAuth.userid,
                                                              uiTargetAuth.discoveryAuth.mutualAuth.password);
                    } else {
                        discObj = new LRBDAuthDiscovery(uiTargetAuth.discoveryAuth.userid,
                                                        uiTargetAuth.discoveryAuth.password,
                                                        discEnabled);
                    }

                    /* Add the discovery entry. */
                    lrbdAuth.discovery = discObj;
                }

                /* Add the tpg entry. */
                lrbdAuth.tpg = tpgObj;
            }

            /* Add our auth entry. */
            this.auth.push(lrbdAuth);
        }
        return true;
    }

    /* Helper method to poulate this.targets. Returns true/false. */
    _populateTargetsFromUI(uiTargetsArr) {
        console.log("_populateTargetsFromUI()");

        for (var i = 0; i < uiTargetsArr.length; i++) {
            var uiTarget = uiTargetsArr[i];

            /* Leaving hosts empty for now. */
            var lrbdTarget = new LRBDTarget(uiTarget.name, null);

            /* Walk the configList of uiTarget and extract selected interfaces.
             * We allow empty hosts array in the LRBDTarget.
             */
            for (var j = 0; j < uiTarget.configList.length; j++) {
                var uiTargetConf = uiTarget.configList[j];

                for (var k = 0; k < uiTargetConf.selectedIntfList.length; k++) {
                    var selectedIntf = uiTargetConf.selectedIntfList[k];

                    /* Finally, create LRBDTargetHost from the selected interface.
                     * Add the LRBDTargetHost to this.hosts if it is not already there.
                     */
                    var lrbdTargetHost = new LRBDTargetHost(selectedIntf.node, "portal-" + selectedIntf.node);
                    if (lrbdTarget.hosts.findIndex(
                        (function(elem, index, arr) {
                            return (elem.host === this.host && elem.portal === this.portal);
                        }),
                        lrbdTargetHost) === -1) {
                        lrbdTarget.hosts.push(lrbdTargetHost);
                    }
                }
            }

            /* Push the newly created LRBDTarget to our targets list. */
            this.targets.push(lrbdTarget);
        }

        return true;
    }

    /* Helper method to poulate this.portals.  Relies on this.targets having been
     * correctly populated.  Returns true/false.
     */
    _populatePortalsFromUI(uiTargetsArr) {
        console.log("_populatePortalsFromUI()");

        /* First populate this.portals with unique LRBDPortal entries.
         * Allowing empty this.portals.
         */
        for (var i = 0; i < this.targets.length; i++) {
            var lrbdTarget = this.targets[i];

            for (var j = 0; j < lrbdTarget.hosts.length; j++) {
                var lrbdTargetHost = lrbdTarget.hosts[j];

                /* Create a new LRBDPortal entry and add it to this.portals
                 * if it is not already there.
                 */
                var lrbdPortal = new LRBDPortal(lrbdTargetHost.portal, null);
                if (this.portals.findIndex(
                    (function(elem, index, arr) {
                        return elem.name === this.name;
                    }),
                    lrbdPortal) === -1) {
                    this.portals.push(lrbdPortal);
                }
            }
        }

        /* Now populate LRBDPortal hosts array from selected interfaces in the UI. */
        for (var i = 0; i < uiTargetsArr.length; i++) {
            var uiTarget = uiTargetsArr[i];

            for (var j = 0; j < uiTarget.configList.length; j++) {
                var uiTargetConfig = uiTarget.configList[j];

                for (var k = 0; k < uiTargetConfig.selectedIntfList.length; k++) {
                    var selectedIntf = uiTargetConfig.selectedIntfList[k];

                    /* Try to find the portals entry that matches the selectedIntf. */
                    var portalIndex = this.portals.findIndex(
                        (function(elem, index, arr) {
                            return elem.name === "portal-" + this.node;
                        }), selectedIntf);

                    /* This is the portal we're looking for.  Append the address of the
                     * selectedIntf if not already present.
                     */
                    if ((portalIndex !== -1) &&
                        (this.portals[portalIndex].addresses.indexOf(selectedIntf.addr) === -1)) {
                        this.portals[portalIndex].addresses.push(selectedIntf.addr);
                    }
                }
            }
        }

        return true;
    }

    /* Helper method to poulate this.pools. Returns true/false. */
    _populatePoolsFromUI(uiTargetsArr) {
        console.log("_populatePoolsFromUI");

        for (var i = 0; i < uiTargetsArr.length; i++) {
            var uiTarget = uiTargetsArr[i];

            for (var j = 0; j < uiTarget.configList.length; j++) {
                var uiTargetConfig = uiTarget.configList[j];

                /* It only makes sense to continue for this config if at least one
                 * image and interface are selected.
                 */
                if (uiTargetConfig.selectedIntfList.length &&
                    uiTargetConfig.selectedImgList.length) {
                    for (var k = 0; k < uiTargetConfig.selectedImgList.length; k++) {
                        var img = uiTargetConfig.selectedImgList[k];
                        var lrbdPool;

                        /* Try to find an LRBDPools instance who's 'pool' instance variable
                         * matches img.pool.  Otherwise, create a new LRBDPool and push it
                         * to this.pools.
                         */
                        var poolsIndex = this.pools.findIndex(
                            (function(elem, index, arr) {
                                return elem.pool === this.pool;
                            }), img);
                        if (poolsIndex !== -1) {
                            lrbdPool = this.pools[poolsIndex];
                        } else {
                            lrbdPool = new LRBDPool(img.pool, null);
                            this.pools.push(lrbdPool);
                        }

                        /* Images are accessed via nodes/interface.  Each node thus needs
                         * a unique LRBDPoolGateway entry key'd by intf.node, to which
                         * we append actual image data in the form of LRBDPoolGatewayTPG
                         * instances.
                         */
                        for (var m = 0; m < uiTargetConfig.selectedIntfList.length; m++) {
                            var intf = uiTargetConfig.selectedIntfList[m];
                            var lrbdPoolGateway;

                            /* Find the appropriate LRBDPoolGateway index in the LRBDPool,
                             * or create and push a new one.
                             */
                            var poolGatewayIndex = lrbdPool.gateways.findIndex(
                                (function(elem, index, arr) {
                                    return elem.host === this.node;
                                }), intf);
                            if (poolGatewayIndex !== -1) {
                                lrbdPoolGateway = lrbdPool.gateways[poolGatewayIndex];
                            } else {
                                lrbdPoolGateway = new LRBDPoolGateway(intf.node, null);
                                lrbdPool.gateways.push(lrbdPoolGateway);
                            }

                            /* If an interface has an initiator list, create and push an LRBDPoolGatewayTPG
                             * entry per initiator.
                             * TODO: need a tie break when: Two identical images selected in separate configs, one with
                             * an initiator(s) the other without - lrbd to handle the tie break, or us?
                             */
                            if (img.initiatorList && img.initiatorList.length) {
                                for (var n = 0; n < img.initiatorList.length; n++) {
                                    var initiator = img.initiatorList[n];

                                    /* Only push if no matching tpg entry present. */
                                    if (lrbdPoolGateway.tpg.findIndex(
                                        (function(elem, index, arr) {
                                            return (elem.portal === (this.intfObj.node + "-portal")) &&
                                                   (elem.image === (this.imgObj.img)) &&
                                                   (elem.initiator === (this.initiator));
                                        }), {"intfObj": intf, "imgObj": img, "initiator": initiator}) === -1) {
                                        lrbdPoolGateway.tpg.push(new LRBDPoolGatewayTPG(intf.node + "-portal", initiator, img.img));
                                    }
                                    
                                }
                            } else {
                                /* Only push if no matching tpg entry present. */
                                if (lrbdPoolGateway.tpg.findIndex(
                                    (function(elem, index, arr) {
                                        return (elem.portal === (this.intfObj.node + "-portal")) && (elem.image === (this.imgObj.img));
                                    }), {"intfObj": intf, "imgObj": img}) === -1) {
                                    lrbdPoolGateway.tpg.push(new LRBDPoolGatewayTPG(intf.node + "-portal", null, img.img));
                                }
                            }
                        }
                    }
                }
            }
        }

        return true;
    }

    /* Populate the LRBDConf instance from a targetsArr representing the current
     * state of the UI.  Returns true on success, false on failure.
     */
    populateFromUI(uiTargetsArr) {
        var ret = true;

        /* Before every populate attempt, clear out the current data. */
        this.setAllEmpty();

        console.log("Populating LRBDConf from UI: " + uiTargetsArr);

        /* Invalid targets array give to us. */
        if (!uiTargetsArr) {
            console.error("Null UI targets array.");
            return false;
        }

        /* While not an error per se, there is not much we can do with an empty
         * targets array.
         */
        if (!uiTargetsArr.length) {
            console.log("Unable to populate LRBDConf from empty UI.");
            return true;
        }

        if (!this._populateTargetsFromUI(uiTargetsArr)) {
            ret = false;
            console.error("Failed to parse UI in order to populate 'targets' section of LRBDConf.");
        }
        if (!this._populatePortalsFromUI(uiTargetsArr)) {
            ret = false;
            console.error("Failed to parse UI in order to populate 'portals' section of LRBDConf.");
        }
        if (!this._populateAuthFromUI(uiTargetsArr)) {
            ret = false;
            console.error("Failed to parse UI in order to populate 'auth' section of LRBDConf.");
        }
        if (!this._populatePoolsFromUI(uiTargetsArr)) {
            ret = false;
            console.error("Failed to parse UI in order to populate 'pools' section of LRBDConf.");
        }

        return ret;
    }
}
