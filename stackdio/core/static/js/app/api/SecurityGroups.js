define(["lib/q", "app/store/stores", "app/model/models"], function (Q, stores, models) {
    return {
        load : function () {
            var self = this;
            var deferred = Q.defer();

            $.ajax({
                url: '/api/security_groups/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var size;

                    deferred.resolve();

                    // Clear the store and the grid
                    stores.SecurityGroup.removeAll();


                    for (i in items) {
                        size = new models.SecurityGroup().create(items[i]);
                        stores.SecurityGroups.push(size);
                    }

                    // Resolve the promise and pass back the loaded items
                    console.log('groups', stores.SecurityGroups());
                    deferred.resolve(stores.SecurityGroups());
                }
            });

            return deferred.promise
        }
    }
});