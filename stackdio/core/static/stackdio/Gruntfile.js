module.exports = function (grunt) {

    grunt.initConfig({
        // Metadata
        pkg: grunt.file.readJSON('package.json'),

        bower: {
            options: {
                action: 'install'
            }
        }
    });

    grunt.loadNpmTasks('grunt-bower-cli');

    grunt.registerTask('install', ['bower']);
};