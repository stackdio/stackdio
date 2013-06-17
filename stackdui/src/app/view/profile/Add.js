Ext.define('stackdio.view.profile.Add', {
    extend  : 'Ext.window.Window',
    alias: 'widget.addProfile',
    
    width   : 600,
    title   : 'Account Profile',
    modal   : true,
    closable: true,
    closeAction: 'hide',
    defaultFocus: 'profile-title',

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
        id: 'profile-form',
        border: false,
        items: [
        {
            xtype:'textfield',
            id: 'profile-title',
            name: 'title',
            fieldLabel: 'Title',
            labelWidth: 150,
            enableKeyEvents: true
        },{
            xtype:'textareafield',
            id: 'profile-description',
            name: 'description',
            fieldLabel: 'Description',
            labelWidth: 150,
            enableKeyEvents: true
        },{
            xtype:        'combo',
            id:           'profile-cloud-provider',
            name:         'cloud_provider',
            hideLabel:    false,
            fieldLabel:   'Account',
            labelWidth:   150,
            store:        'ProviderAccounts',
            displayField: 'title',
            valueField:   'id',
            queryMode:    'local',
            editable:     false
        },{
            xtype:'textfield',
            id: 'profile-ami',
            name: 'image_id',
            fieldLabel: 'AMI',
            labelWidth: 150,
            enableKeyEvents: true
        },{
            xtype:        'combo',
            id:           'profile-instance-size',
            name:         'default_instance_size',
            hideLabel:    false,
            fieldLabel:   'Default Instance Size',
            labelWidth:   150,
            store:        'InstanceSizes',
            displayField: 'title',
            valueField:   'id',
            queryMode:    'local',
            editable:     false
        },{
            xtype:        'combo',
            id:           'profile-script',
            name:         'script',
            hideLabel:    false,
            fieldLabel:   'Script',
            labelWidth:   150,
            store:        'ProfileScripts',
            displayField: 'script',
            valueField:   'script',
            queryMode:    'local',
            editable:     false
        },{
            xtype:'textfield',
            id: 'profile-ssh-user',
            name: 'ssh_user',
            fieldLabel: 'SSH User',
            labelWidth:   150,
            enableKeyEvents: true
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
        id: 'save-profile',
        iconCls: 'save-icon'
    }]
});

