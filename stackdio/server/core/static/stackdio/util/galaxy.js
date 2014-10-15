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

define(['q', 'knockout', 'postal'], function (Q, ko, postal) {
    var DuplicateViewRegistrationException = function (message) {
       this.message = message;
       this.name = "DuplicateViewRegistrationException";
    };

    var UnregisteredViewWarning = function (message) {
       this.message = message;
       this.name = "UnregisteredViewWarning";
    };

    var MissingViewModelException = function (message) {
       this.message = message;
       this.name = "MissingViewModelException";
    };

    var MissingDOMElementException = function (message) {
       this.message = message;
       this.name = "MissingDOMElementException";
    };

    var ViewLoadedException = function (message) {
       this.message = message;
       this.name = "ViewLoadedException";
    };

    var MissingOptionException = function (message) {
       this.message = message;
       this.name = "MissingOptionException";
    };

    var $galaxy = function (options) {
        var self = this;

        if (options && options.hasOwnProperty('channel') && options.channel !== '') {
            this.network = postal.channel(options.channel);
        } else {
            this.network = postal.channel('galaxy');
        }

        // Handle errors when require tries to load a view model id that is invalid
        requirejs.onError = function (err) {
            console.error(err);
            console.error(new MissingViewModelException('Unable to find the location of `' + self.currentLocation + '.js`.'));
        };

        // Detect when the hash changes
        window.addEventListener('popstate', function (event) {
            self.parseHash();
        });

        if (options && options.hasOwnProperty('viewmodelDirectory')) {
            this.viewmodelDirectory = options.viewmodelDirectory;
        } else {
            this.viewmodelDirectory = 'viewmodel';
        }

        if (options && options.hasOwnProperty('viewDirectory')) {
            this.viewDirectory = options.viewDirectory;
        } else {
            this.viewDirectory = 'view';
        }

        this.currentPayload = null;
        this.federation = [];
        this.currentLocation = null;
        
        this.parseHash();

        // If view specified in URL hash isn't registered, require it now (which will automatically register it)
        var exists = this.federation.map(function (view) {
            if (view.id === self.currentLocation) {
                return view;
            }
        });

        if (!exists.length && this.currentLocation !== null) {
            require([this.viewmodelDirectory + '/' + this.currentLocation], function (vm) {});
        }
    };

    $galaxy.prototype.parseHash = function () {
        var self = this;
        var redirectAfterParse = false;

        /*
         *   Parse the location.hash to find the view id and any additional 
         *   key/value pairs in the URL parameters to pass to the view model
         */
        var grabHash = location.hash.split('#')[1];

        if (grabHash && this.currentLocation && (this.currentLocation !== grabHash.split('&')[0])) {
            redirectAfterParse = true;
        }

        if (grabHash) {
            this.currentLocation = grabHash.split('&')[0];
            var urlParamArray = grabHash.split('&');
            urlParamArray.splice(0,1);

            this.currentPayload = urlParamArray.map(function (kv) {
                var a = {}, k = kv.split('=')[0], v = kv.split('=')[1];
                a[k] = v;
                return a;
            }).reduce(function (prev,curr) {
                for (var key in curr) {
                    prev[key] = curr[key];
                }
                return prev;
            }, {});
        }

        // redirectAfterParse should only be true on browser history change
        if (redirectAfterParse) {
            this.render(this.currentLocation);
        }
    };

    $galaxy.prototype.transport = function (options) {
        var hashBuilder = [];

        try {
            // If the argument is a string, assume it's the location for transport 
            if (options && typeof options === 'string') {
                this.currentLocation = options;
            } else if (options && typeof options === 'object' && !options.hasOwnProperty('location')) {
                throw new MissingOptionException('You must provide a location property and a payload property when publishing the `transport` event with an object parameter.');
            } else if (options && typeof options === 'object' && options.hasOwnProperty('location')) {
                this.currentLocation = options.location;
            }

            hashBuilder[hashBuilder.length] = this.currentLocation;   // Start building the location hash

            if (options.hasOwnProperty('payload') && options.payload) {
                this.currentPayload = options.payload;
                for (var key in options.payload) {    // Add each k/v pair as a URL hash parameter
                    var param = options.payload[key];
                    hashBuilder[hashBuilder.length] = '&' + key + '=' + param;
                }
            }

            window.location.hash = hashBuilder.join('');  // Set the location hash
            this.render(this.currentLocation);            // Render the view
        } catch (ex) {
            console.error(ex);                
        }
    };

    $galaxy.prototype.getDOMElements = function (id) {
        var bindingType = (id.substr(0,1) === '.') ? 'class' : 'id';
        var undecoratedDomBindingId = id.replace(/[\.#]/, '');
        var elements = [];

        if (bindingType === 'class') {
            var byClass = document.getElementsByClassName(undecoratedDomBindingId);
            if (byClass.length) {
                for (var el in byClass) {
                    if (typeof byClass[el] === 'object') {
                        elements[elements.length] = byClass[el];
                    }
                }
            }
        } else if (bindingType === 'id') {
            elements[elements.length] = document.getElementById(undecoratedDomBindingId);
        }

        if (elements[elements.length-1] === null) {
            throw new MissingDOMElementException('The DOM element you specified ('+id+') for view model `'+this.currentLocation+'` was not found.')
        }

        return elements;
    };

    $galaxy.prototype.join = function (viewmodel) {
        var self = this;

        if (!viewmodel.hasOwnProperty('__joined')) {
            
            // If a view model defined any children, join them first, and mark them as children
            if (viewmodel.hasOwnProperty('children') && viewmodel.children.length > 0) {
                viewmodel.children.map(function (child) {
                    child.__parent = viewmodel.id;
                });
            }

            // Add a __loaded property to keep track of which models have already been bound and loaded into DOM
            if (!viewmodel.hasOwnProperty('__loaded')) {
                viewmodel.__loaded = false;
            }

            // Give each model a show method that delegates to the internal join() function
            if (!viewmodel.hasOwnProperty('show')) {
                viewmodel.show = function () {
                    self.render(this.id);
                };
            }

            // Add the viewmodel to the internal registry
            viewmodel.__joined = true;
            self.federation.push(viewmodel);
            this.network.publish(viewmodel.id + '.joined');

            // Immediately render any module marked with autoRender (usually navigation elements)
            if (viewmodel.hasOwnProperty('autoRender') && viewmodel.autoRender) {
                self.render(viewmodel.id);
            }

            // location.hash has a view id in it, and the current view matches it.  Render view.
            if (self.currentLocation !== null && viewmodel.id === self.currentLocation) {
                self.render(viewmodel.id);
            }

            // Nothing in the location.hash, and current view marked as default. Render view.
            if (self.currentLocation === null && viewmodel.hasOwnProperty('defaultView') && viewmodel.defaultView) {
                self.currentLocation = viewmodel.id;
                self.render(viewmodel.id);
            }

        // View already joined
        } else {
            if (!viewmodel.hasOwnProperty('__parent')) {
                console.warn('The view model with id `' + viewmodel.id + '` has already joined the federation.');
            }
        }
    };

    $galaxy.prototype.leave = function (id) {
        var exists = _.findWhere(this.federation, {id: id});

        if (exists) {
            this.federation = _.filter(this.federation, function (vm) {
                vm.id !== id;
            });
        }
    };

    $galaxy.prototype.render = function (id) {
        var self = this;
        var currentViewModel = null;

        // Capture current view and hide all others (not autoRender views)
        self.federation.forEach(function (view) {
            if (view.id === id) {
                currentViewModel = view;
            } else if (!view.autoRender && view.id !== self.currentLocation) {
                self.getDOMElements(view.domBindingId).forEach(function (el) {
                    el.style.display = 'none';
                });
            }
        });

        // Ensure the view model's HTML template is loaded and has been bound
        self.load(id).then(function () {
            // After view is loaded, ensure it is visible
            self.getDOMElements(currentViewModel.domBindingId).forEach(function (el) {
                el.style.display = '';
            });

            // Render any children views/widgets
            if (currentViewModel.hasOwnProperty('children')) {
                currentViewModel.children.map(function (child) {
                    self.render(child.id);
                });
            }

            self.network.publish(currentViewModel.id + '.docked', self.currentPayload);

        }).fail(function (ex) {
            console.error(ex);
        }).catch(function (ex) {
            console.error(ex);
        }).finally(function () { });
    };

    $galaxy.prototype.load = function (id) {
        var self = this;
        var deferred = Q.defer();
        var viewmodel = _.findWhere(self.federation, {id: id});

        if (viewmodel) {
            if (!viewmodel.loaded) {
                var viewTemplate = [this.viewDirectory, viewmodel.templatePath].join('');

                self.getDOMElements(viewmodel.domBindingId).forEach(function (el) {
                    var xhr = new XMLHttpRequest();     // Create XHR object
                    xhr.open('GET', viewTemplate, true);    // GET the HTML file for the view model
                    xhr.onloadend = function (evt) {    // After it's loaded
                        if (evt.target.status === 200 || evt.target.status === 302) {
                            el.innerHTML = evt.target.responseText;             // Inject the HTML
                            ko.applyBindings(viewmodel, el);                    // Bind view model to DOM
                            viewmodel.loaded = true;                            // Flag view model as loaded
                            self.network.publish(viewmodel.id + '.arrived');    // Notify subscribers of arrived event
                            deferred.resolve();                                 // Resolve promise
                        }
                    };

                    xhr.send();
                });
            } else {
                this.network.publish(viewmodel.id + '.arrived');
                deferred.resolve();
            }
        } else { 
            console.warn(new UnregisteredViewWarning('Location with id `' + id + '` has not joined the federation. Attempting to join in now.'));
            require([self.viewmodelDirectory + '/' + id], function (vm) {});
        }

        return deferred.promise;
    };

    return new $galaxy({
        viewmodelDirectory: 'viewmodel',
        viewDirectory: '/static/stackdio/view/'
    });
});
