// -----------------------------------------------------------------------------
//    ds-policy-ed.js
//
//    DeepSea policy.cfg editor element.
// -----------------------------------------------------------------------------

Polymer({
    is: "ds-policy-ed",

    properties: {
        // Array of ds-policy.js::Minion objects representing available DeepSea minions.
        minions: {
            type: Array,
            value: []
        },
        // Array of ds-policy.js::Role objects representing available DeepSea roles.
        // Roles can be taken on by any Minion.
        roles: {
            type: Array,
            value: []
        },
        // Array of ds-policy.js::Profile objects representing available DeepSea hardware profiles.
        // Profiles are not necessarily applicable to all Minions.
        profiles: {
            type: Array,
            value: []
        },
    },

    // Get cluster proposal data.
    ready: function() {
        console.log(this.is + ": ready.");

        // Grab cluster proposal from DeepSea.
        if (this.getClusterProposal() !== true) {
            // TBD
        }
    },

    // Generates some phony data  now.
    // TODO: Remove this once we have a DeepSea runner.
    _getPhonyClusterProposal: function() {
        var minions = [];
        var roles = [];
        var profiles = {};

        for (var i = 9; i > 0; i--) {
            minions.push("wf-test-minion-" + i);
        }
        for (var i = 9; i > 0; i--) {
            roles.push("wf-test-role-" + i);
        }
        for (var i = 1; i < 4; i++) {
            profiles["wf-test-profile-" + i] = []
            for (var j = i; j < i + 3; j++) {
                profiles["wf-test-profile-" + i].push("wf-test-minion-" + j);
            }
        }

        return { "minions": minions, "roles": roles, "profiles": profiles };
    },

    // Find (by id string) and return a reference to a Minion in this.minions.
    // null is returned if Minion not found.
    _getMinionById: function(id) {
        ret = null;

        var minionIndex = this.minions.findIndex((function(elem, index, arr) {
            return elem.compare(this) === 0;
        }), id);

        if (minionIndex !== -1) {
            ret = this.minions[minionIndex];
        }

        return ret;
    },

    // Populate this.minions array with Minion objects instantiated from minion id's.
    // These references will be used within Role and Profile minion lists.
    _parseClusterMinions: function(minions) {
        var minionObjs = [];
        var ret = true;

        for (var i = 0; i < minions.length; i++) {
            minionObjs.push(new Minion(minions[i])); // isMaster = false isMember = true
        }

        // Sort using Minion comparison.
        minionObjs.sort((function(minion1, minion2) {
            return minion1.compare(minion2);
        }));

        // TODO: Need to determine from DeepSea which minion is the master.  Likely via a secondary
        // ajax call to determin 'master_minion', or we'll augment the 'cluster' JSON format.  For
        // now, just setting the first one as the master.
        if (minionObjs.length) {
            minionObjs[0].isMaster = true;
        }

        // Finally, save our minions.
        this.set("minions", minionObjs);

        return ret;
    },

    // Populate this.roles array with Role objects instantiated from role names.
    // For each role, we will pass the this.minions array to be set as the role's
    // availableMinions array.  A role's selectedMinions will be populated from a policy.
    _parseClusterRoles: function(roles) {
        var roleObjs = [];
        var ret = true;

        for (var i = 0; i < roles.length; i++) {
            roleObjs.push(new Role(roles[i], this.minions));
        }

        // Sort using Role comparison.
        roleObjs.sort((function(role1, role2) {
            return role1.compare(role2);
        }));

        // Finally, save our roles.
        this.set("roles", roleObjs);

        return ret;
    },

    // Populate this.profiles array with Profile objects instantiated from profile names.
    // A profile's availableMinions must also be populated using this.minions references
    // that match the minion id's found in profiles[$profileName].  selectedMinions will
    // be populated from a policy.
    _parseClusterProfiles: function(profiles) {
        var profileObjs = [];
        var ret = true;

        for (profile in profiles) {
            // Find all the Minion objects that match this profile's available minion id's.
            var pMinions = [];

            // Find corresponding this.minions reference to minion id found in profiles[profile] array.
            for (var i = 0; i < profiles[profile].length; i++) {
                var minion = this._getMinionById(profiles[profile][i]);

                // If we've found the corresponding reference, push it to pMinions.
                if (minion) {
                    // No need to sort this, as Role/Profile creation will also sort it's
                    // available/selectedMinions arrays.
                    pMinions.push(minion);
                } else {
                    // ERROR: We trust DeepSea, so we should not get here.  In case we do, however,
                    // don't stop, rather alert the caller of an error.
                    console.error(this.is + ": minion " + profiles[profile][i] + " not found in cluster minion array!");
                    ret = false;
                }
            }

            // When creating the new Profile, pass the list of this.minions references that can take on ths profile.
            profileObjs.push(new Profile(profile, pMinions));
        }

        // Sort using Role/Profile comparison.
        profileObjs.sort((function(profile1, profile2) {
            return profile1.compare(profile2);
        }));

        // Finally, save our profiles.
        this.set("profiles", profileObjs);

        return ret;
    },

    // Parse:
    // { "minions"  : [ "minion-1", ... ],                                             --> All available minions.
    //   "roles"    : [ "role-x", ... ],                                               --> All available roles.
    //   "profiles" : { "profile-x": [ "minion-m", ... ], ... },                       --> All available profiles and which minions can take on this profile.
    //   "policy"   : { "member_minions": [ "minion-m", ... ],                         --> Selected cluster member minions (policy.cfg).
    //                  "roles"         : { "role-x": [ "minion-m", ... ], ... },      --> Selected roles and which minions will take on each role (policy.cfg).
    //                  "profiles"      : { "profile-x": [ "minion-m", ... ], ... },   --> Selected profiles and which minions will take on each role (policy.cfg).
    // }
    // Populates minions, roles, profiles.
    _parseClusterProposal: function(cluster) {
        var ret = true;

        // Populate Minions.
        ret = this._parseClusterMinions(cluster.minions) && ret;
        // Populate Roles.
        ret = this._parseClusterRoles(cluster.roles) && ret;
        // Populate Profiles
        ret = this._parseClusterProfiles(cluster.profiles) && ret;
        // TODO: If we obtained a policy, populate that as well.

        return ret;
    },

    // Obtain cluster proposal data from DeepSea and populate minions, roles and profiles.
    // FIXME: For now this is hardcoded data.
    getClusterProposal: function() {
        var ret = true;
        var cluster = this._getPhonyClusterProposal();

        console.log(this.is + ": Populating cluster proposal.");

        // Sanity check cluster parameter.  "policy" can be null if policy.cfg does not yet exist.
        if (!cluster.minions || !cluster.roles || !cluster.profiles) {
            console.error(this.is + ": Cluster proposal incomplete.");
            alert("Failed to receive complete cluster proposal.  DeepSea discovery stage not run?");
            ret = false;
        }

        // Parse the cluster JSON object, provided we have a vaild cluster structure.
        if (ret && this._parseClusterProposal(cluster) !== true) {
            console.error(this.is + ": Failed to parse cluster proposal.");
            alert("Invalid cluster proposal received.  DeepSea discovery stage failure?");
            ret = false;
        }

        return ret;
    },

    // Used to determine if a given Minion can take on a Profile.  Since a Minion which has
    // been selected for a given Profile is moved off the available array and onto the
    // selected array, we check for both here.
    isMinionAvailableForProfile: function(profile, minion) {
        return profile.isMinionAvailable(minion) || profile.isMinionSelected(minion);
    }
});
