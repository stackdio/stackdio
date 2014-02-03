define(['jquery', 'q', 'knockout', 'util/postOffice'], function ($, Q, ko, _O_) {
    var DuplicateViewRegistrationException = function (message) {
       this.message = message;
       this.name = "DuplicateViewRegistrationException";
    };

    var UnregisteredViewException = function (message) {
       this.message = message;
       this.name = "UnregisteredViewException";
    };

    var ViewLoadedException = function (message) {
       this.message = message;
       this.name = "ViewLoadedException";
    };

    var MissingOptionException = function (message) {
       this.message = message;
       this.name = "MissingOptionException";
    };

    var SixtySix = function (options) {
        var self = this;

        self.options = options;
        self.registeredViews = [];
        self.viewParser = [];
        self.defaultView = null;
        self.currentView = null;

        self.hashParser = location.hash.split('#')[1]

        if (self.hashParser) {
            self.viewParser = self.hashParser.split('.');

            if (self.viewParser.length === 2) {
                self.currentView = self.hashParser;
            }
        }
    };

    SixtySix.prototype.navigate = function (options) {
        var self = this;

        try {
            if (!options.hasOwnProperty('view')) {
                throw new MissingOptionException('You must provide a view property and a data property when publishing the `navigate` event.');
            }
            if (!options.hasOwnProperty('data')) {
                console.warn('You did not provide any data in the options for your `navigate` event.');
            }

            // Set the location hash to the current view id
            window.location.hash = options.view;

            // Set view as the current one
            self.currentView = options.view;

            // Render the view
            self.render(options.view);

        } catch (ex) {
            console.error(ex);                
        }
    };

    SixtySix.prototype.register = function (viewmodel) {
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

    SixtySix.prototype.unregister = function (id) {
        var self = this;
        var exists = _.findWhere(self.registeredViews, {id: id});

        if (exists) {
            this.registeredViews = _.filter(self.registeredViews, function (vm) {
                vm.id !== id;
            });
        }
    };

    SixtySix.prototype.render = function (id) {
        var self = this;
        var currentViewModel = null;

        self.registeredViews.forEach(function (view) {
            // Find the view model currently being rendered
            if (view.id === id) {
                currentViewModel = view;

            // If not the current view, and not an autoLoad view, hide the view
            } else if (!view.autoRender && view.id !== self.currentView) {
                $(view.domBindingId).hide();
            }
        });

        // Ensure the view model's HTML template is loaded and has been bound
        this.load(id).then(function () {

            // After view is loaded, ensure it, and each child view, is visible
            $(currentViewModel.domBindingId).show();

            if (currentViewModel.hasOwnProperty('children')) {
                currentViewModel.children.map(function (child) {
                    self.render(child.id);
                });
            }
        }).fail(function (ex) {
            console.error(ex);
        }).finally(function () {
            // Clean up code goes here
        });
    };

    SixtySix.prototype.load = function (id) {
        var self = this;
        var deferred = Q.defer();
        var viewmodel = _.findWhere(self.registeredViews, {id: id});

        if (viewmodel) {
            if (!viewmodel.loaded) {
                var template = '/static/stackdio/view/' + viewmodel.templatePath;
                var bindElement = $(viewmodel.domBindingId);

                bindElement.load(template, function (text, status, xhr) {
                    ko.applyBindings(viewmodel, bindElement.get(0));
                    viewmodel.loaded = true;
                    _O_.publish(viewmodel.id + '.loaded');
                    deferred.resolve();
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

    return new SixtySix();
});
