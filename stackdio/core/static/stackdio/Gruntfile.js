module.exports = function (grunt) {

    grunt.initConfig({
        // Metadata
        pkg: grunt.file.readJSON('package.json'),

        run_grunt: {
            knockout: {
                options: {
                    log: false,
                    process: function (res) {
                        if (res.fail) {
                            res.output = 'new content'
                            grunt.log.writeln('Failed to build knockout', res);
                        }
                    }
                },
                src: ['components/knockoutjs/Gruntfile.js']
            },
            q: {
                options: {
                    log: false,
                    process: function (res) {
                        if (res.fail) {
                            res.output = 'new content'
                            grunt.log.writeln('Failed to build knockout', res);
                        }
                    }
                },
                src: ['components/q/Gruntfile.js']
            }
        },

        bower: {
            options: {
                action: 'install'
            }
        }
    });

    grunt.loadNpmTasks('grunt-bower-cli');
    grunt.loadNpmTasks('grunt-run-grunt');

    grunt.registerTask('install', ['bower']);
    grunt.registerTask('configure', ['run_grunt']);
};