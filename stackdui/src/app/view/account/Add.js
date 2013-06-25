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
            anchor: '100%',
            labelWidth: 130
        },
        id: 'account-form',
        items: [
        {
            xtype:'textfield',
            id: 'account-title',
            name: 'title',
            fieldLabel: 'Title',
            enableKeyEvents: true
        },{
            xtype:'textareafield',
            id: 'account-description',
            name: 'description',
            fieldLabel: 'Description',
            enableKeyEvents: true
        },{
            xtype:'textfield',
            name: 'access_key_id',
            fieldLabel: 'AWS Access Key'
        },{
            xtype:'textfield',
            name: 'secret_access_key',
            fieldLabel: 'AWS Secret Key'
        },{
            xtype:'textfield',
            name: 'keypair',
            fieldLabel: 'AWS Keypair Name'
        },{
            xtype:'textfield',
            name: 'security_groups',
            fieldLabel: 'Security Groups'
        },{
            xtype:'textfield',
            name: 'route53_domain',
            fieldLabel: 'Route 53 Domain'
        },{
            xtype:'filefield',
            name: 'private_key_file',
            fieldLabel: 'Private Key File'
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
    },{
        text: 'Save &amp; Add Another',
        id: 'save-account-add',
        iconCls: 'save-icon'
    }]
});

