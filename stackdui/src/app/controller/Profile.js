Ext.define('stackdio.controller.Profile', {
    extend: 'Ext.app.Controller',


    init: function () {
        var me = this;

        me.profileWindow = Ext.widget('profileWindow');


        /*

              ____ ___  _   _ _____ ____   ___  _        _     ___   ____ ___ ____ 
             / ___/ _ \| \ | |_   _|  _ \ / _ \| |      | |   / _ \ / ___|_ _/ ___|
            | |  | | | |  \| | | | | |_) | | | | |      | |  | | | | |  _ | | |    
            | |__| |_| | |\  | | | |  _ <| |_| | |___   | |__| |_| | |_| || | |___ 
             \____\___/|_| \_| |_| |_| \_\\___/|_____|  |_____\___/ \____|___\____|

        */
        me.control({

            '#profiles-button': {
                click: function (btn, e) {
                    me.profileWindow.show();
                }
            }

            ,'#save-profile': {
                click: function (btn, e) {
                    var verb, urlSuffix = '', r, rec, record = me.profileForm.down('form').getForm().getValues();

                    if (record.hasOwnProperty('id')) {
                        verb = 'PUT';
                        urlSuffix = me.selectedProfile.data.id + '/';
                    } else {
                        verb = 'POST';
                    }

                    record.cloud_provider = me.providerAccount;

                    StackdIO.request({
                        url: Settings.api_url + '/api/profiles/' + urlSuffix,
                        method: verb,
                        jsonData: record,
                        success: function (response) {
                            var res = Ext.JSON.decode(response.responseText);
                            if (res.hasOwnProperty('id')) {
                                me.application.notification.howl('Profile saved...', 2000);
                                btn.up('window').hide();
                                Ext.getStore('AccountProfiles').load();
                            } else {
                                me.application.notification.scold('Profile did not save. Update your data and try again', 3000);
                            }
                        },
                        failure: function (response) {
                            me.application.notification.scold('Profile did not save. Update your data and try again', 3000);
                        }
                    });
                }
            }

            ,'profileList': {
                itemdblclick : function (grid, item, domEl, evt, eopts, fn) {
                    me.selectedProfile = grid.getSelectionModel().getSelection()[0];
                    me.showProfileForm(me.selectedProfile);
                }
            }

        });


        /*

                 _______     _______ _   _ _____    _   _    _    _   _ ____  _     _____ ____  ____  
                | ____\ \   / / ____| \ | |_   _|  | | | |  / \  | \ | |  _ \| |   | ____|  _ \/ ___| 
                |  _|  \ \ / /|  _| |  \| | | |    | |_| | / _ \ |  \| | | | | |   |  _| | |_) \___ \ 
                | |___  \ V / | |___| |\  | | |    |  _  |/ ___ \| |\  | |_| | |___| |___|  _ < ___) |
                |_____|  \_/  |_____|_| \_| |_|    |_| |_/_/   \_\_| \_|____/|_____|_____|_| \_\____/
        
        */

        /*
         *      Add accounts to the new profile split buttons once store is loaded
         */
        me.getProviderAccountsStore().on('load', function (store, records, successful, eOpts) {
            var t, type;
            var btn = Ext.getCmp('create-profile');
             
            for (t in records) {
                type = records[t];
                btn.menu.add({
                    text: type.data.title,
                    id: 'profileaccount-' + type.data.id,
                    handler: function () {
                        me.application.fireEvent('stackdio.newprofile', this.id.split('-')[1]);
                    }
                })
            }
        });

        me.application.addListener('stackdio.newprofile', function (accountId) {
            if (accountId === null) {
                accountId = me.getProviderAccountsStore().getAt(0).data.id;
            }

            me.providerAccount = accountId;
            me.showProfileForm();
        });

        me.application.addListener('stackdio.showprofiles', function () {
            me.profileWindow.show();
        });

    },



    /*

              ____ ___  _   _ _____ ____   ___  _     _     _____ ____     _____ _   _ _   _  ____ _____ ___ ___  _   _ ____  
             / ___/ _ \| \ | |_   _|  _ \ / _ \| |   | |   | ____|  _ \   |  ___| | | | \ | |/ ___|_   _|_ _/ _ \| \ | / ___| 
            | |  | | | |  \| | | | | |_) | | | | |   | |   |  _| | |_) |  | |_  | | | |  \| | |     | |  | | | | |  \| \___ \ 
            | |__| |_| | |\  | | | |  _ <| |_| | |___| |___| |___|  _ <   |  _| | |_| | |\  | |___  | |  | | |_| | |\  |___) |
             \____\___/|_| \_| |_| |_| \_\\___/|_____|_____|_____|_| \_\  |_|    \___/|_| \_|\____| |_| |___\___/|_| \_|____/ 

    */

    showProfileForm: function (record) {
        var me = this; 

        if (!me.hasOwnProperty('profileForm')) {
            me.profileForm = Ext.widget('addProfile');
        }

        me.profileForm.show();

        if (typeof record !== 'undefined') {
            me.profileForm.down('form').getForm().loadRecord(record);
        }
    },




    /*

             ____    ___   _   _   ____    ___   _   _    ____   ____  
            | __ )  |_ _| | \ | | |  _ \  |_ _| | \ | |  / ___| / ___| 
            |  _ \   | |  |  \| | | | | |  | |  |  \| | | |  _  \___ \ 
            | |_) |  | |  | |\  | | |_| |  | |  | |\  | | |_| |  ___) |
            |____/  |___| |_| \_| |____/  |___| |_| \_|  \____| |____/ 


    */
    views: [
         'profile.List'
        ,'profile.Add'
        ,'profile.Window'
    ],

    models: [
        'AccountProfile'
    ],

    stores: [
        'AccountProfiles'
        ,'ProviderAccounts'
        ,'InstanceSizes'
    ],


    /*

             ____    _____   _____   _____   ____    _____   _   _    ____   _____   ____  
            |  _ \  | ____| |  ___| | ____| |  _ \  | ____| | \ | |  / ___| | ____| / ___| 
            | |_) | |  _|   | |_    |  _|   | |_) | |  _|   |  \| | | |     |  _|   \___ \ 
            |  _ <  | |___  |  _|   | |___  |  _ <  | |___  | |\  | | |___  | |___   ___) |
            |_| \_\ |_____| |_|     |_____| |_| \_\ |_____| |_| \_|  \____| |_____| |____/ 

    */
    refs: [
        {
            ref: 'newProfile', selector: '#create-profile'
        }
    ]
});


