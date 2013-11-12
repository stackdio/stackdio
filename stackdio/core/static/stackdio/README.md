# stackd.io user interface

## Installation

### Prerequisites

#### Node.js
You need to have Node.js installed on your system, or otherwise installing stackd.io user interface is a painfully tedious manual process.

### Installing Grunt and Bower
Once you have Node installed, you need to grab the [Grunt](http://gruntjs.com/getting-started) module, and the [Bower](http://bower.io/) module.

    npm install -g grunt-cli bower

### Installing stackd.io npm modules
In your CLI, get to the **core/static/stackdio** directory and install all npm modules.

    npm install
    
### Installing all Bower components
Next, you can run a Grunt task, from the same directory, to get all the Bower components installed.

    grunt install
    
### Configure Knockout and Q
All other Bower modules include a minified version out of the box, so we need to minify Knockout and Q by first going to each module and installing all the Node modules required.

First we run *npm install* for Knockout which will build the minified version.

    cd components/knockout
    npm install
    
Change to the Q directory and run the *npm install* command which will create the minified version.
    
    cd ../q
    npm install
    
Then go back to the root stackdio application directory.
    
    cd ../..
    
## Running development server
Now that everything is installed and minified, you can run the local Django server.

    python manage.py runserver
    
