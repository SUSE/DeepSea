// ds-policy.js
// ------------

'use strict';

// -----------------------------------------------------------------------------
// Salt/DeepSea data structures
// -----------------------------------------------------------------------------

// A Salt minion.  By default it's:
//   - not the master minion
//   - is a cluster member
class Minion {
    constructor(id, isMaster = false, isMember = true) {
        this.id = String(id);
        this.isMaster = isMaster;
        this.isMember = isMember;
    }

    // Compare yourself to another minion based on id.  Returns -1 if less than,
    // 1 if greater, 0 if equal.
    compare(minion) {
        var ret = -1; // Assume we're less than minion.
        // slice() simplifies "[object Type]" to "Type"
        var minionType = Object.prototype.toString.call(minion).slice(8, -1);
        var compareId;

        if (minionType === "Object") {
            // Ensure minion.id exists, or we're comparing something that may not
            // be a Minion.
            if (minion.id) {
                compareId = minion.id;
            } else {
                // In this odd case, we'll end up returning -1 causing the element
                // to be pushed below us.
                compareId = null;
            }
        } else if (minionType === "String") {
            compareId = minion;
        }

        if (this.id > compareId) {
            ret = 1;
        } else if (this.id == compareId) {
            ret = 0;
        }

        return ret;
    }
}

// A DeepSea role.
class Role {
    constructor(name, availableMinions = [], selectedMinions = []) {
        this.name = String(name);
        this.availableMinions = availableMinions.sort(this._compareMinions);
        this.selectedMinions = selectedMinions.sort(this._compareMinions);
    }

    // Passed to findIndex() in order to find a Minion by name within an array.
    _findMinionByName(elem, index, arr) {
        return elem.compare(this) === 0;
    }

    // Passed to findIndex() in order to find a Minion by reference within an array.
    _findMinion(elem, index, arr) {
        return this === elem;
    }

    // Passed as a compare function to sort().
    _compareMinions(minion1, minion2) {
        return minion1.compare(minion2);
    }

    // Move a Minion from fromArr to toArr.
    _moveMinion(index, fromArr, toArr) {
        var mRef = fromArr.splice(index, 1)[0];
        toArr.push(mRef);
        toArr.sort(this._compareMinions);
    }

    // Add Minion by id to the selectedMinions array.  This will remove it from
    // the availableMinions array.  Returns true/false.
    selectMinionById(id) {
        var ret = false;

        // Search availableMinions array for Minion by id.
        var index = this.availableMinions.findIndex(this._findMinionByName, id);

        // If found, remove it from the availableMinions array.
        if (index !== -1) {
            this._moveMinion(index, this.availableMinions, this.selectedMinions);
            ret = true;
        }

        // Return true/false.
        return ret;
    }

    // Add a Minion by reference to the selectedMinions array.  This will remove
    // it from the availableMinions array.  Returns true/false.
    selectMinion(minionRef) {
        var ret = false;

        // Search availableMinions array for minionRef.
        var index = this.availableMinions.findIndex(this._findMinion, minionRef);

        // If found, remove it from the availableMinions array.
        if (index !== -1) {
            this._moveMinion(index, this.availableMinions, this.selectedMinions);
            ret = true;
        }

        // Return true/false.
        return ret;
    }

    // Remove a Minion by id from the selectedMinions array and return it
    // to the availableMinions array.  Returns true/false.
    deSelectMinionById(id) {
        var ret = false;

        // Search selectedMinions array for Minion by id.
        var index = this.selectedMinions.findIndex(this._findMinionByName, id);

        // If found, remove it from the selectedMinions array.
        if (index !== -1) {
            this._moveMinion(index, this.selectedMinions, this.availableMinions);
            ret = true;
        }

        // Return true/false.
        return ret;
    }

    // Remove a Minion by reference from the selectedMinions array and return it
    // to the availableMinions array.  Returns true/false.
    deSelectMinion(minionRef) {
        var ret = false;

        // Search selectedMinions array for minionRef.
        var index = this.selectedMinions.findIndex(this._findMinion, minionRef);

        // If found, remove it from the selectedMinions array.
        if (index !== -1) {
            this._moveMinion(index, this.selectedMinions, this.availableMinions);
            ret = true;
        }

        // Return true/false.
        return ret;
    }

    // Check if minionRef is contained within our availalbeMinions array.  Return
    // true/false;
    isMinionAvailable(minionRef) {
        return this.availableMinions.findIndex(this._findMinion, minionRef) !== -1;
    }

    // Check if minionRef is contained within our selectedMinions array.  Return
    // true/false;
    isMinionSelected(minionRef) {
        return this.selectedMinions.findIndex(this._findMinion, minionRef) !== -1;
    }

    // Compare yourself to another role based on name.  Returns -1 if less than,
    // 1 if greater, 0 if equal.
    compare(role) {
        var ret = -1; // Assume we're less than minion.
        // slice() simplifies "[object Type]" to "Type"
        var roleType = Object.prototype.toString.call(role).slice(8, -1);
        var compareName;

        if (roleType === "Object") {
            // Ensure role.name exists, or we're comparing something that may not
            // be a Role.
            if (role.name) {
                compareName = role.name;
            } else {
                // In this odd case, we'll end up returning -1 causing the element
                // to be pushed below us.
                compareName = null;
            }
        } else if (roleType === "String") {
            compareName = role;
        }

        if (this.name > compareName) {
            ret = 1;
        } else if (this.name == compareName) {
            ret = 0;
        }

        return ret;
    }
}

// A DeepSea HW Profile.
class Profile extends Role {
    constructor(name, availableMinions = [], selectedMinions = []) {
        super(name, availableMinions, selectedMinions);
    }
}
