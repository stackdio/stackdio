Ext.define('stackdio.view.account.Add', {
    extend  : 'Ext.window.Window',
    alias: 'widget.addAccount',
    
    width   : 800,
    title   : 'Provider Account',
    modal   : true,
    closable: true,
    closeAction: 'hide',
    defaultFocus: 'account-title',

    defaults: {
        padding: '10'
    },

    layout: 'fit',

    items: [{
        xtype: 'form',
        layout: 'anchor',
        defaults: {
            anchor: '100%'
        },
        id: 'account-form',
        items: [
        {
            xtype:        'combo',
            name:         'provider_type',
            hideLabel:    false,
            fieldLabel:   'Provider',
            labelWidth:   110,
            store:        'ProviderTypes',
            displayField: 'title',
            valueField:   'id',
            queryMode:    'local',
            editable:     false
        },{
            xtype:'textfield',
            id: 'account-title',
            name: 'title',
            fieldLabel: 'Title',
            labelWidth: 110,
            enableKeyEvents: true
        },{
            xtype:'textareafield',
            id: 'account-description',
            name: 'description',
            fieldLabel: 'Description',
            labelWidth: 110,
            enableKeyEvents: true
        },{
            xtype:'textfield',
            name: 'access_key_id',
            fieldLabel: 'AWS Access Key',
            labelWidth: 110
        },{
            xtype:'textfield',
            name: 'secret_access_key',
            fieldLabel: 'AWS Secret Key',
            labelWidth: 110
        },{
            xtype:'textfield',
            name: 'keypair',
            fieldLabel: 'AWS Keypair Name',
            labelWidth: 110
        },{
            xtype:'textfield',
            name: 'security_groups',
            fieldLabel: 'Security Groups',
            labelWidth: 110
        },{
            xtype:'textfield',
            name: 'route53_domain',
            fieldLabel: 'Route 53 Domain',
            labelWidth: 110
        },{
            xtype:'filefield',
            name: 'private_key_file',
            fieldLabel: 'Private Key File',
            labelWidth: 110
        }]
    }],

    buttons: [{
        text: 'Cancel',
        iconCls: 'cancel-icon',
        handler: function (btn) {
            btn.up('window').hide();
        }
    },{
        text: 'Save',
        id: 'save-account',
        iconCls: 'save-icon'
    }]
});

