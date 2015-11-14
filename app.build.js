{
    appDir: 'stackdio/ui/static/stackdio/app',
    mainConfigFile: 'stackdio/ui/static/stackdio/app/main.js',
    dir: 'stackdio/ui/static/stackdio/build',
    modules: [
        {
            name: 'main',
            include: [
                'bloodhound',
                'bootbox',
                'bootstrap',
                'domReady',
                'fuelux',
                'jquery',
                'knockout',
                'ladda',
                'moment',
                'select2',
                'spin',
                'typeahead',
                'underscore',
                'utils/mobile-fix',
                'utils/class',
                'utils/utils',
                'utils/bootstrap-growl',
                'generics/pagination',
            ]
        }
    ]
}