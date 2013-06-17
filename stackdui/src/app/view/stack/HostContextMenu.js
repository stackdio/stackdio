Ext.define('stackdio.view.stack.HostContextMenu', {
    extend: 'Ext.menu.Menu',
    alias: 'widget.hostContextMenu',
    
    items: [{
        text: 'Delete',
        id: 'delete-stack-host',
        iconCls: 'icon-remove-sign'
    }]
}); 