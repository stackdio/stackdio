Ext.define('stackdio.view.stack.Add', {
    extend  : 'Ext.window.Window',
    alias: 'widget.addStack',
    
    width   : 800,
    title   : 'Stack',
    modal   : true,
    closable: true,
    closeAction: 'hide',
    defaultFocus: 'stack-title',

    defaults: {},
    layout: 'anchor',

    items: [
        {
            xtype: 'form',
            layout: 'anchor',
            padding: '10',
            border: false,
            anchor: '100% 70%',
            defaults: {
                anchor: '100%'
            },
            id: 'stack-form',
            items: [
            {
                xtype:'textfield',
                id: 'stack-title',
                name: 'title',
                fieldLabel: 'Title',
                labelWidth: 110,
                enableKeyEvents: true
            },{
                xtype:'textareafield',
                id: 'stack-description',
                name: 'description',
                fieldLabel: 'Description',
                labelWidth: 110,
                enableKeyEvents: true
            }]
        },
        {
            xtype: 'splitbutton'
            ,id: 'create-stack-host'
            ,text: 'New Host'
            ,ui: 'info'
            ,scale: 'small'
            ,iconCls: 'icon-plus-sign'
            ,style: 'float: right; margin: 10px 10px 0 0'
            ,menu: {}
            ,width: 130
        },
        {
            xtype: 'launchedStackHosts'
            ,hidden: true
        },
        {
            xtype: 'newStackHosts'
            ,hidden: true
        }
    ],

    buttons: [{
        text: 'Cancel',
        iconCls: 'cancel-icon',
        handler: function (btn) {
            btn.up('window').hide();
        }
    },{
        text: 'Save',
        id: 'save-stack',
        iconCls: 'save-icon'
    }]
});

