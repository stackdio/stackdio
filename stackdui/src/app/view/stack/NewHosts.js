Ext.define('stackdio.view.stack.NewHosts', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.newStackHosts',
    

    autoScroll: true,
    store: 'StackHosts',
    anchor: '100% 30%',
    padding: '10',
    stripeRows: true,
    columns: [
        {
            header: 'Roles',
            dataIndex: 'roles',
            flex: 2
            ,renderer: function (ids, metaData, record, rowIndex, colIndex, store, view) {
                var r, rr = [], store = Ext.getStore('Roles'), k = ids.split(',');

                if (k.length && k[0] !== '') {
                    for (r in k) {
                        rr.push(store.getAt(store.findExact('id', parseInt(k[r], 10))).data.title);
                    }
                }

                return rr.join(',');
            }
        },
        {
            header: 'Count',
            dataIndex: 'count',
            flex: 1
        },
        {
            header: 'Profile',
            dataIndex: 'cloud_profile',
            flex: 2
            ,renderer: function (id, metaData, record, rowIndex, colIndex, store, view) {
                var store = Ext.getStore('AccountProfiles'), title = '', index = store.findExact('id', id);

                console.log(index);
                if (~index) {
                    title = store.getAt(index).data.title;
                } 

                return title;
            }
        },
        {
            header: 'Size',
            dataIndex: 'instance_size',
            flex: 3
            ,hidden: true
            ,renderer: function (id, metaData, record, rowIndex, colIndex, store, view) {
                var store = Ext.getStore('InstanceSizes'), size = '', index = store.findExact('id', id);

                if (~index) {
                    size = store.getAt(index).data.title;
                }

                return '<div style="white-space:normal !important;">' + size + '</div>';
            }
        },
        {
            header: 'Host Pattern'
            ,dataIndex: 'hostname'
            ,flex: 1
            ,hidden: true
        },
        {
            header: 'Security Groups'
            ,dataIndex: 'security_groups'
            ,flex: 2
            ,hidden: true
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

