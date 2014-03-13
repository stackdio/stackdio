define(['q', 'model/models'], function (Q, models) {
    return {
        load : function (stack) {
            var deferred = Q.defer();

            $.ajax({
                url: stack.hosts,
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response.results);
                }
            });

            return deferred.promise;
        },
        save: function (record, stack) {
            var deferred = Q.defer();

            $.ajax({
                url: stack.hosts,
                type: 'PUT',
                data: record,
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response);
                }
            });

            return deferred.promise;
        },
        delete: function (record, stack) {
            var deferred = Q.defer();

            $.ajax({
                url: stack.hosts,
                type: 'DELETE',
                data: {
                    id: record.id
                },
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response);
                }
            });

            return deferred.promise;
        }
    }
});