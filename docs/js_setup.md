# Installation

## Prerequisites

### Node.js
You need to have [Node.js](http://nodejs.org/) and [npm](https://npmjs.org/) installed on your system.

On Ubuntu, both Node and npm can be installed from apt-get

```bash
# Ubuntu
sudo apt-get install nodejs
```

On CentOS, you have to install them separately
```bash
sudo yum install nodejs npm
```

## Installing bower
In your CLI, run the following command to install bower:

```bash
npm install -g bower
```

### Directory
You must be in the site-packages directory to do this.  To get there, run the following commands:

```bash
workon stackdio
cdsitepackages
cd stackdio
```

### Installing stackd.io Bower components
Next, you can run bower to get all the Bower components installed.

```bash
bower install
```
