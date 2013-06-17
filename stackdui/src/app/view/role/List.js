Ext.define('stackdio.view.role.List', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.roleList',
    store: 'Roles',

    autoScroll: true,

    // tbar: [
    //     {
    //         xtype: 'button',
    //         text: 'New Role',
    //         iconCls: 'add-icon',
    //         id: 'create-role'
    //     }
    // ],

    columns: [
        { 
            header: 'Title',
            dataIndex: 'title',
            flex: 1
        },
        { 
            header: 'Description',
            dataIndex: 'description',
            flex: 4
        }
    ]
});


