define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'store/stores',
    'api/api'
],
function (Q, ko, base, _O_, stores, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.stores = stores;
        self.userCanModify = ko.observable();
        self.osChoices = [
            {
                id: 'ext2',
                title: 'ext2'
            },
            {
                id: 'ext3',
                title: 'ext3'
            },
            {
                id: 'ext4',
                title: 'ext4'
            },
            {
                id: 'fuse',
                title: 'fuse'
            },
            {
                id: 'xfs',
                title: 'xfs'
            }
        ];

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'snapshot.list';
        self.templatePath = 'snapshots.html';
        self.domBindingId = '#snapshot-list';

        try {
            self.$66.register(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */

        // Query OPTIONS on /providers and if DELETE is not in allowed verb list, user is not admin
        API.Snapshots.options()
            .then(function (allowed) {
                self.userCanModify(allowed.verbs.indexOf('DELETE') !== -1);
            });

        self.addSnapshot = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            record.account = self.selectedAccount;

            console.log('record',record);

            API.Snapshots.save(record)
                .then(function () {
                    $("#snapshot-form-container").dialog("close");
                    self.showSuccess();
                })
                .catch(function (error) {
                    $("#alert-error").show();
                });
        };

        self.removeSnapshot = function (snapshot) {
            API.Snapshots.delete(snapshot)
                .then(self.showSuccess)
                .catch(function (error) {
                    $("#alert-error").show();
                });
        };

    };

    vm.prototype = new base();
    return new vm();
});
