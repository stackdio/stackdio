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

define(function() {
    return {
        recursive_update: function(d, u) {
            for (var k in u) {
                if (u[k] instanceof Object) {
                    if (d[k] == null) {
                        var r = this.recursive_update({}, u[k]);
                    } else {
                        var r = this.recursive_update(d[k], u[k]);
                    }
                    d[k] = r;
                } else {
                    d[k] = u[k];
                }
            }
            return d;
        }
    };
});