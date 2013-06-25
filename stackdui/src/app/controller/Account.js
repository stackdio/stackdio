Ext.define('stackdio.controller.Account', {
    extend: 'Ext.app.Controller',


    init: function () {
        var me = this;


        /*

              ____ ___  _   _ _____ ____   ___  _        _     ___   ____ ___ ____ 
             / ___/ _ \| \ | |_   _|  _ \ / _ \| |      | |   / _ \ / ___|_ _/ ___|
            | |  | | | |  \| | | | | |_) | | | | |      | |  | | | | |  _ | | |    
            | |__| |_| | |\  | | | |  _ <| |_| | |___   | |__| |_| | |_| || | |___ 
             \____\___/|_| \_| |_| |_| \_\\___/|_____|  |_____\___/ \____|___\____|

        */
        me.control({

            '#create-account': {
                click: function (btn, e) {
                    // me.showAccountForm();
                }
            },
            
            '#save-account': {
                click: function (btn, e) {
                    var closeOnSuccess = true;

                    e.preventDefault();
                    e.stopPropagation();

                    me.createAccount(closeOnSuccess);
                }
            },

            '#save-account-add': {
                click: function (btn, e) {
                    var closeOnSuccess = false;
                    
                    e.preventDefault();
                    e.stopPropagation();

                    me.createAccount(closeOnSuccess);
                }
            },

            'accountList': {
                itemdblclick : function (grid, item, domEl, evt, eopts, fn) {
                    me.selectedAccount = grid.getSelectionModel().getSelection()[0];
                    me.showAccountForm(me.selectedAccount);
                }
            },

            '#accounts-button': {
                click: function (btn, e) {
                    Ext.getCmp('content-area').getLayout().setActiveItem(1);
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
         *      Add provider types to the new account split buttons once store is loaded
         */
        me.getProviderTypesStore().on('load', function (store, records, successful, eOpts) {
            var t, type, types;
            var btn = Ext.getCmp('create-account');
            var mnu = btn.menu;
             
            for (t in records) {
                type = records[t];
                btn.menu.add({
                    text: type.data.title,
                    id: 'providertype-' + type.data.id,
                    handler: function () {
                        me.application.fireEvent('stackdio.newaccount', this.id.split('-')[1]);
                    }
                })
            }
        });

        me.application.addListener('stackdio.newaccount', function (typeId) {
            me.providerType = typeId;
            me.showAccountForm();
        });

    },



    /*

              ____ ___  _   _ _____ ____   ___  _     _     _____ ____     _____ _   _ _   _  ____ _____ ___ ___  _   _ ____  
             / ___/ _ \| \ | |_   _|  _ \ / _ \| |   | |   | ____|  _ \   |  ___| | | | \ | |/ ___|_   _|_ _/ _ \| \ | / ___| 
            | |  | | | |  \| | | | | |_) | | | | |   | |   |  _| | |_) |  | |_  | | | |  \| | |     | |  | | | | |  \| \___ \ 
            | |__| |_| | |\  | | | |  _ <| |_| | |___| |___| |___|  _ <   |  _| | |_| | |\  | |___  | |  | | |_| | |\  |___) |
             \____\___/|_| \_| |_| |_| \_\\___/|_____|_____|_____|_| \_\  |_|    \___/|_| \_|\____| |_| |___\___/|_| \_|____/ 

    */
    createAccount: function (closeOnSuccess) {
        var me = this;
        var i, r, rec, record = me.accountForm.down('form').getForm().getValues();
        var files, formData = new FormData(), xhr = new XMLHttpRequest();

        // A reference to the files selected
        files = me.accountForm.down('filefield').fileInputEl.dom.files;

        // Append each file to the FormData() object
        for (i = 0; i < files.length; i++) {
            formData.append('private_key_file', files[i]);
        }

        // Add the provider type that the user chose from the account split button
        formData.append('provider_type', me.providerType);

        // Append all other required fields to the form data
        for (r in record) {
            rec = record[r];
            formData.append(r, rec);
        }

        // Open the connection to the provider URI and set authorization header
        xhr.open('POST', 'http://localhost:8000/api/providers/');
        xhr.setRequestHeader('Authorization', 'Basic ' + Base64.encode('testuser:password'));

        // Define any actions to take once the upload is complete
        xhr.onloadend = function (evt) {
            var response_data;

            // Show an animated message containing the result of the upload
            if (evt.target.status === 200 || evt.target.status === 201 || evt.target.status === 302) {
                me.application.notification.howl('New account saved.', 1000);
                if (closeOnSuccess) me.accountForm.destroy();
                me.getProviderAccountsStore().load();
            } else {
                var html=[], response = JSON.parse(evt.target.response);

                for (key in response) {
                    failure = response[key];
                    html.push('<p>' + key + ': ' + failure + '</p>');
                }
                me.application.notification.scold('New account failed to save. Check your data and try again...'+html, 5000);
            }
        };

        // Start the upload process
        xhr.send(formData);
    },

    showAccountForm: function (record) {
        var me = this; 

        if (!me.hasOwnProperty('accountForm')) {
            me.accountForm = Ext.widget('addAccount');
        }

        me.accountForm.show();

        if (typeof record !== 'undefined') {
            console.log(record);
            me.accountForm.down('form').getForm().loadRecord(record);
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
         'account.List'
        ,'account.Add'
    ],

    models: [
         'ProviderAccount'
        ,'ProviderType'
    ],

    stores: [
         'ProviderAccounts'
        ,'ProviderTypes'
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
            ref: 'newAccount', selector: '#create-account'
        }
    ]
});


