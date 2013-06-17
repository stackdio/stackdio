"use strict"

Ext.require([
    'Ext.button.Split',
    'Ext.chart.Chart',
    'Ext.chart.axis.Numeric',
    'Ext.chart.axis.Category',
    'Ext.chart.series.Line',
    'Ext.container.ButtonGroup',
    'Ext.container.Viewport',
    'Ext.layout.container.Anchor',
    'Ext.layout.container.Border',
    'Ext.layout.container.Column',
    'Ext.layout.container.Form',
    'Ext.menu.Menu',
    'Ext.form.field.ComboBox',
    'Ext.form.field.Text',
    'Ext.form.field.Radio',
    'Ext.form.Panel',
    'Ext.form.RadioGroup',
    'Ext.grid.column.Template',
    'Ext.grid.plugin.DragDrop',
    'Ext.grid.RowNumberer',
    'Ext.resizer.Splitter',
    'Ext.selection.CheckboxModel',
    'Ext.toolbar.Spacer',
    'Ext.util.Cookies',
    'Ext.util.MixedCollection',
    'Ext.util.AbstractMixedCollection',
    'Ext.util.Filter',
    'Ext.util.Observable',
    'Ext.util.Sorter',
    'Ext.util.Sortable',
    'Ext.ux.form.MultiSelect',
    'Ext.ux.RowExpander',
    'feature.grouping',
    'feature.rowbody',
    'feature.feature',
    'feature.rowwrap',
    'stackdio.tool.AnimatedMessage',
    'stackdio.tool.AuthenticatedConnection',
    'stackdio.tool.HowlNotification'
]);

var StackdIO;

Ext.onReady(function () {

    StackdIO = Ext.widget('apiRequest');

    Ext.application({
        controllers: [
            'Application'
        ],

        name: 'stackdio',
        autoCreateViewport: true,

        launch: function() {
            var me = this;
            me.animatedMessage = Ext.widget('notify');

            // Enable the focus manager
            Ext.FocusManager.enable();

            me.commandKeyMap = new Ext.util.KeyMap(Ext.getBody(), [
                // {
                //     key: "f",
                //     handler: function (code, e) {
                //         var field = Ext.ComponentManager.get('filter-terms');
                //         var nonTrackingFields = ['master-label',
                //                                  'document-labels',
                //                                  'prediction-document-labels',
                //                                  'resource-master-label',
                //                                  'resource-document-labels',
                //                                  'add-document-labels',
                //                                  'segment-labels',
                //                                  'metadata-type',
                //                                  'metadata-value',
                //                                  'filter-terms',
                //                                  'newModelName',
                //                                  'trainingSetName',
                //                                  'resourceSetName'];

                //         if (nonTrackingFields.indexOf(Ext.FocusManager.focusedCmp.id) === -1) {
                //             e.preventDefault();
                //             field.focus();
                //             field.selectText();
                //         }
                //     }
                // },
                {
                    key: "m",
                    ctrl: true,
                    shift: true,
                    handler: function (code, e) {
                        me.fireEvent('DRSI.Training.BuildNewModel');
                    }
                }
            ]);
        }
    });
});