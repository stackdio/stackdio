Ext.define('stackdio.view.snapshot.Add', {
    extend  : 'Ext.window.Window',
    alias: 'widget.addSnapshot',
    
    width   : 800,
    title   : 'New snapshot',
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
                name: 'title',
                fieldLabel: 'Title',
                labelWidth: 110,
                enableKeyEvents: true
            }
            ,{
                xtype:'textareafield',
                name: 'description',
                fieldLabel: 'Description',
                labelWidth: 110,
                enableKeyEvents: true
            }
            ,{
                xtype:'textfield',
                name: 'snapshot_id',
                fieldLabel: 'ID',
                labelWidth: 110
            }
            ,{
                xtype:'textfield',
                name: 'size_in_gb',
                fieldLabel: 'Size (in GB)',
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
        id: 'save-snapshot',
        iconCls: 'save-icon'
    }]
});

