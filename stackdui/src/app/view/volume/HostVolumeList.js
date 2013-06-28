Ext.define('stackdio.view.volume.HostVolumeList', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.hostVolumeList',
    store: 'Volumes',

    autoScroll: true,

    columns: [
        { 
            header: 'Device',
            dataIndex: 'device',
            flex: 1
        },
        { 
            header: 'Mount Point',
            dataIndex: 'mount_point',
            flex: 1
        },
        { 
            header: 'Snapshot',
            dataIndex: 'snapshot',
            flex: 1
            ,renderer: function (ids, metaData, record, rowIndex, colIndex, store, view) {
                var r, store = Ext.getStore('Snapshots');

                r = store.findRecord('id', record.data.snapshot).data.title;

                return r;
            }
        }
    ]
});


