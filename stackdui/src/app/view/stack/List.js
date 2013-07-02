Ext.define('stackdio.view.stack.List', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.stackList',
    store: 'Stacks',

    autoScroll: true,

    columns: [
        { 
            header: 'Title',
            dataIndex: 'title',
            flex: 1
        },
        { 
            header: 'Purpose',
            dataIndex: 'description',
            flex: 3
        },
        { 
            header: 'Status',
            dataIndex: 'status',
            flex: 1
        },
        {
            xtype: 'actioncolumn',
            width: 25,
            items: [{
                icon: '/img/icons/delete.png',  // Use a URL in the icon config
                tooltip: 'Delete',
                handler: function (grid, rowIndex, colIndex) {

                }
            }]
        }
    ]
});


