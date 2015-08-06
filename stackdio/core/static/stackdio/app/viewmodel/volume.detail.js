/*!
  * Copyright 2014,  Digital Reasoning
  * 
  * Licensed under the Apache License, Version 2.0 (the "License");
  * you may not use this file except in compliance with the License.
  * You may obtain a copy of the License at
  * 
  *     http://www.apache.org/licenses/LICENSE-2.0
  * 
  * Unless required by applicable law or agreed to in writing, software
  * distributed under the License is distributed on an "AS IS" BASIS,
  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  * See the License for the specific language governing permissions and
  * limitations under the License.
  * 
*/

define([
    '../../bower_components/q/q',
    'knockout',
    'util/galaxy',
    'util/form',
    'store/Blueprints',
    'store/HostVolumes',
    'store/Snapshots',
    'store/BlueprintHosts',
    'api/api',
    'model/models'
],
function (Q, ko, $galaxy, formutils, BlueprintStore, VolumeStore, SnapshotStore, BlueprintHostStore, API, models) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedBlueprint = ko.observable();
        self.blueprintTitle = ko.observable();
        self.selectedHost = ko.observable();
        self.hostTitle = ko.observable();
        self.$galaxy = $galaxy;
        self.volumeIds = ['/dev/xvdj','/dev/xvdk','/dev/xvdm','/dev/xvdn'];

        self.BlueprintStore = BlueprintStore;
        self.VolumeStore = VolumeStore;
        self.SnapshotStore = SnapshotStore;
        self.BlueprintHostStore = BlueprintHostStore;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'volume.detail';
        self.templatePath = 'volume.html';
        self.domBindingId = '#volume-detail';

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            SnapshotStore.populate().then(function () {
                self.init(data);
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {
            var blueprint = null;
            var host = null;

            if (data.hasOwnProperty('blueprint')) {
                blueprint = BlueprintStore.collection().filter(function (p) {
                    return p.id === parseInt(data.blueprint, 10)
                })[0];

                self.blueprintTitle(blueprint.title);
            } else {
                self.blueprintTitle('New Blueprint');
            }
            self.selectedBlueprint(blueprint);


            if (data.hasOwnProperty('host')) {
                host = BlueprintHostStore.collection().filter(function (h) {
                    return h.id === parseInt(data.host, 10)
                })[0];

                self.hostTitle(host.title);
            } else {
                self.hostTitle('New Host');
            }
            self.selectedHost(host);

        };

        self.addVolume = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            var volume = new models.BlueprintHostVolume().create({
                snapshot: record.volume_snapshot.value,
                device: record.volume_device.value,
                mount_point: record.volume_mount_point.value
            });

            VolumeStore.add(volume);

            $('#volume_snapshot').attr('selectedIndex', '-1').find("option:selected").removeAttr("selected");
            $('#volume_device').val('');
            $('#volume_mount_point').val('');

            $galaxy.transport('host.detail');
        };

        self.cancelChanges = function (model, evt) {
            $galaxy.transport('host.detail');
        };
    };
    return new vm();
});
