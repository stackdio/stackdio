# Installation

## Prerequisites

### Node.js
You need to have [Node.js](http://nodejs.org/) and [npm](https://npmjs.org/) installed on your system, or otherwise installing Synthesys is a painfully tedious manual process.

On Ubuntu, both Node and npm can be installed from apt-get

    sudo apt-get install nodejs

On CentOS, you have to install them separately

    sudo yum install nodejs npm

### Git
Some dependencies of the UI are not in the Bower repository, so they need to be pulled directly from Github. Therefore, you need to ensure you have Git installed.

    sudo apt-get install git  <-- Ubuntu
    sudo yum install git      <-- CentOS

## Pulling dependencies

### Installing Grunt and Bower
Once you have Node installed, you need to grab the [Grunt](http://gruntjs.com/getting-started) module, and the [Bower](http://bower.io/) module.

    npm install -g grunt-cli bower

### Installing stackd.io dependencies
In your CLI, get to the directory where you cloned the project and look in the `core/static/stackdio` directory. To install all packages, you just need to run the setup screipt.

    npm run-script setup
    
## Low memory process
If you are running on a low memory machine, or most of the memory is already being used while you're trying to install, you may receive the following message while installing.

    Error: spawn ENOMEM
    
This is caused because `npm` and `bower` both spawn new processes to run the install scripts, so if you are geting the error, you can try to manually run the steps that the setup script runs to conserve memory.

### Installing stackd.io npm modules
In your CLI, get to the `core/static/stackdio` directory and install all npm modules.

    npm install
    
### Installing all Bower components
Next, you can run a Grunt task, from the same directory, to get all the Bower components installed.

    grunt install
    
### Configure Knockout and Q
All other Bower modules include a minified version out of the box, so we need to minify Knockout and Q by first going to each module and installing all the Node modules required.

First we run the build for Knockout which will produce the minified version.

    cd components/knockout
    npm install
    
Change to the Q directory and run the build command which will create the minified version.
    
    cd ../q
    npm install
    
Then go back to the root stackdio application directory.
    
    cd ../..

        
# Running stackd.io

## Start development server
Now that everything is installed and minified, you can run the local Django server.

    python manage.py runserver

This starts the application on port 8000.

## Start using it
Now you hit the local development URI to see the user interface: [http://localhost:8000/](http://localhost:8000/)