Ext.define('stackdio.view.volume.Add', {
    extend  : 'Ext.window.Window',
    alias: 'widget.addVolume',
    
    width   : 800,
    title   : 'Attachable Volume',
    modal   : true,
    closable: true,
    closeAction: 'hide',
    defaultFocus: 'volume-title',

    defaults: {
        padding: '10'
    },

    layout: 'fit',

    items: [{
        xtype: 'form',
        id: 'volume-form',
        border: false,
        layout: 'anchor',
        defaults: {
            anchor: '100%'
        },
        items: [
            {
                xtype:'textfield',
                id: 'volume-title',
                name: 'count',
                fieldLabel: 'Count',
                labelWidth: 110
            }
        ]
    }],

    buttons: [{
        text: 'Cancel',
        iconCls: 'cancel-icon',
        handler: function (btn) {
            btn.up('window').hide();
        }
    },{
        text: 'Save',
        id: 'save-volume',
        iconCls: 'save-icon'
    }]
});

