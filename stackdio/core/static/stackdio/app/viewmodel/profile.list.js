/*!
  * Copyright 2014,  Digital Reasoning
  * 
  * Licensed under the Apache License, Version 2.0 (the "License");
  * you may not use this file except in compliance with the License.
  * You may obtain a copy of the License at
  * 
  *     http://www.apache.org/licenses/LICENSE-2.0
  * 
  * Unless required by applicable law or agreed to in writing, software
  * distributed under the License is distributed on an "AS IS" BASIS,
  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  * See the License for the specific language governing permissions and
  * limitations under the License.
  * 
*/

define([
    '../../bower_components/q/q',
    'knockout',
    'bootbox',
    'util/galaxy',
    'util/alerts',
    'store/Accounts',
    'store/Profiles',
    'api/api'
],
function (Q, ko, bootbox, $galaxy, alerts, AccountStore, ProfileStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedAccount = ko.observable(null);
        self.userCanModify = ko.observable(true);
        self.$galaxy = $galaxy;
        self.isSuperUser = stackdio.settings.superuser;

        self.AccountStore = AccountStore;
        self.ProfileStore = ProfileStore;
        self.EnhancedProfileStore = ko.observableArray();

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'profile.list';
        self.templatePath = 'profiles.html';
        self.domBindingId = '#profile-list';

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            self.EnhancedProfileStore.removeAll();

            AccountStore.populate().then(function () {
                return ProfileStore.populate();
            }).then(function () {
                self.init(data);
            }).catch(function (error) {
                console.log(error)
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */
        self.init = function (data) {
            self.EnhancedProfileStore.removeAll();

            if (data && data.hasOwnProperty('account')) {
                ProfileStore.collection().forEach(function (profile) {
                    profile.account = _.findWhere(AccountStore.collection(), { id: profile.cloud_provider });
                    if (profile.account.id === parseInt(data.account, 10)) {
                        self.EnhancedProfileStore.push(profile);
                    }
                });
            } else {
                ProfileStore.collection().forEach(function (profile) {
                    if (!profile.hasOwnProperty('image_id')) {
                        profile.image_id = 'n/a';
                    }
                    profile.account = _.findWhere(AccountStore.collection(), { id: profile.cloud_provider });
                    self.EnhancedProfileStore.push(profile);
                });
            }

        };

        self.createProfile = function (account) {
            $galaxy.transport({
                location: 'profile.detail',
                payload: {
                    account: account.id
                }
            });
        };

        self.deleteProfile = function (profile) {
            bootbox.confirm("Please confirm that you want to delete this profile.", function (result) {
                if (result) {
                    API.Profiles.delete(profile).then(function () {
                        ProfileStore.removeById(profile.id);
                        self.init();
                    })
                    .catch(function (error) {
                        alerts.showMessage('#error', error, true);
                    });
                }
            });
        };

        self.viewProfile = function (profile) {
            $galaxy.transport({
                location: 'profile.detail',
                payload: {
                    profile: profile.id
                }
            });
        };

        self.refresh = function() {
            ProfileStore.populate(true);
        };
    };
    return new vm();
});
