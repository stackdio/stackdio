define(function() {
    return {
        recursive_update: function(d, u) {
            for (var k in u) {
                if (u[k] instanceof Object) {
                    if (d[k] == null) {
                        var r = this.recursive_update({}, u[k]);
                    } else {
                        var r = this.recursive_update(d[k], u[k]);
                    }
                    d[k] = r;
                } else {
                    d[k] = u[k];
                }
            }
            return d;
        }
    };
});