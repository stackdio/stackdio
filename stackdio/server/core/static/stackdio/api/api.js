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
        "api/SecurityGroups", 
        "api/Users", 
        "api/Regions",
        "api/InstanceSizes", 
        "api/Profiles", 
        "api/Accounts", 
        "api/ProviderTypes", 
        "api/Snapshots", 
        "api/StackHosts", 
        "api/Formulas", 
        "api/Stacks",
        "api/Search",
        "api/Blueprints"
        ], 
    function (SecurityGroups, Users, Regions, InstanceSizes, Profiles, Accounts, ProviderTypes, Snapshots, StackHosts, Formulas, Stacks, Search, Blueprints) {

    return {
        SecurityGroups: SecurityGroups,
        Users: Users,
        Regions: Regions,
        InstanceSizes: InstanceSizes,
        Profiles:      Profiles,
        Accounts:      Accounts,
        ProviderTypes: ProviderTypes,
        Snapshots:     Snapshots,
        StackHosts:    StackHosts,
        Formulas:      Formulas,
        Stacks:        Stacks,
        Search:        Search,
        Blueprints:    Blueprints
    }
});