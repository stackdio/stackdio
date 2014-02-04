define(['q', 'knockout', 'util/postOffice'], function (Q, ko, _O_) {
    var DuplicateViewRegistrationException = function (message) {
       this.message = message;
       this.name = "DuplicateViewRegistrationException";
    };

    var UnregisteredViewException = function (message) {
       this.message = message;
       this.name = "UnregisteredViewException";
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

    var $66 = function () {
        this.registeredViews = [];
        this.currentView = location.hash.split('#')[1] || null;
        this.currentPayload = null;
    };

    $66.prototype.navigate = function (options) {
        var hashBuilder = [];

        try {
            if (!options.hasOwnProperty('view')) {
                throw new MissingOptionException('You must provide a view property and a data property when publishing the `navigate` event.');
            }
            if (!options.hasOwnProperty('data')) {
                console.warn('You did not provide any data in the options for your `navigate` event.');
            }
           
            this.currentView = options.view;
            hashBuilder[hashBuilder.length] = options.view;   // Start building the location hash

            if (options.data) {
                this.currentPayload = options.data;
                for (var key in options.data) {    // Add each k/v pair as a URL hash parameter
                    var param = options.data[key];
                    hashBuilder[hashBuilder.length] = '&' + key + '=' + param;
                }
            }

            window.location.hash = hashBuilder.join('');  // Set the location hash
            this.render(options.view);                    // Render the view
        } catch (ex) {
            console.error(ex);                
        }
    };

    $66.prototype.getDOMElements = function (id) {
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
            throw new MissingDOMElementException('The DOM element you specified ('+id+') for view model `'+this.currentView+'` was not found.')
        }

        return elements;
    };

    $66.prototype.register = function (viewmodel) {
        var self = this;

        if (!viewmodel.hasOwnProperty('__registered')) {
            
            // If a view model defined any children, register them first, and mark them as children
            if (viewmodel.hasOwnProperty('children') && viewmodel.children.length > 0) {
                viewmodel.children.map(function (child) {
                    child.__parent = viewmodel.id;
                });
            }

            // Add a __loaded property to keep track of which models have already been bound and loaded into DOM
            if (!viewmodel.hasOwnProperty('__loaded')) {
                viewmodel.__loaded = false;
            }

            // Give each model a show method that delegates to the internal register() function
            if (!viewmodel.hasOwnProperty('show')) {
                viewmodel.show = function () {
                    self.render(this.id);
                };
            }

            // Add the viewmodel to the internal registry
            viewmodel.__registered = true;
            self.registeredViews.push(viewmodel);
            _O_.publish(viewmodel.id + '.registered');

            // Immediately render any module marked with autoRender (usually navigation elements)
            if (viewmodel.hasOwnProperty('autoRender') && viewmodel.autoRender) {
                self.render(viewmodel.id);
            }

            // location.hash has a view id in it, and the current view matches it.  Render view.
            if (self.currentView !== null && viewmodel.id === self.currentView) {
                self.render(viewmodel.id);
            }

            // Nothing in the location.hash, and current view marked as default. Render view.
            if (self.currentView === null && viewmodel.hasOwnProperty('defaultView') && viewmodel.defaultView) {
                self.currentView = viewmodel.id;
                self.render(viewmodel.id);
            }

        // View already registered
        } else {
            if (!viewmodel.hasOwnProperty('__parent')) {
                console.warn('The view model with id `' + viewmodel.id + '` is already registered.');
            }
        }
    };

    $66.prototype.unregister = function (id) {
        var exists = _.findWhere(this.registeredViews, {id: id});

        if (exists) {
            this.registeredViews = _.filter(this.registeredViews, function (vm) {
                vm.id !== id;
            });
        }
    };

    $66.prototype.render = function (id) {
        var self = this;
        var currentViewModel = null;

        // Capture current view and hide all others (not autoRender views)
        self.registeredViews.forEach(function (view) {
            if (view.id === id) {
                currentViewModel = view;
            } else if (!view.autoRender && view.id !== self.currentView) {
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

            _O_.publish(currentViewModel.id + '.rendered', self.currentPayload);

        }).fail(function (ex) {
            console.error(ex);
        }).finally(function () { });
    };

    $66.prototype.load = function (id) {
        var self = this;
        var deferred = Q.defer();
        var viewmodel = _.findWhere(self.registeredViews, {id: id});

        if (viewmodel) {
            if (!viewmodel.loaded) {
                var template = '/static/stackdio/view/' + viewmodel.templatePath;

                self.getDOMElements(viewmodel.domBindingId).forEach(function (el) {
                    var xhr = new XMLHttpRequest();     // Create XHR object
                    xhr.open('GET', template, true);    // GET the HTML file for the view model
                    xhr.onloadend = function (evt) {    // After it's loaded
                        if (evt.target.status === 200 || evt.target.status === 302) {
                            el.innerHTML = evt.target.responseText;     // Inject the HTML
                            ko.applyBindings(viewmodel, el);            // Bind view model to DOM
                            viewmodel.loaded = true;                    // Flag view model as loaded
                            _O_.publish(viewmodel.id + '.loaded');      // Notify subscribers of load event
                            deferred.resolve();                         // Resolve promise
                        }
                    };

                    xhr.send();
                });
            } else {
                _O_.publish(viewmodel.id + '.loaded');
                deferred.resolve();
            }
        } else { 
            deferred.reject(new UnregisteredViewException('View with id `' + id + '` has not been registered and cannot be loaded.'));
        }

        return deferred.promise;
    };

    return new $66();
});
