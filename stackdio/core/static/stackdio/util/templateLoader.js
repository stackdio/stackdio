define(['knockout', 'app/global_settings'],

function (ko, global_settings) {

    return {
        load : function (target, templateURL, vm, callback) {
            console.log('Binding ', target, ' to ', templateURL);
            $(target).load(global_settings.templateRoot + templateURL, function () {
                ko.applyBindings(vm, document.querySelector(target));

                if (callback) {
                    callback.call(document.querySelector(target));
                }
            });
        }
    }
});