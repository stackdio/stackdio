# Preparing Ubuntu for stackd.io installation

The steps below were written using Ubuntu 13.10 from a Ubuntu-provided AMI on Amazon Web Services (AWS). The exact AMI we used is `ami-2f252646`, and you should be able to easily launch an EC2 instance using this AMI from the [AWS EC2 Console](https://console.aws.amazon.com/ec2/home?region=us-east-1#launchAmi=ami-2f252646).

# Prerequisites

All of these steps require `root` or `sudo` access.  Before installing anything
with `apt-get` you should run `apt-get update` first.

### MySQL

> **NOTE**: Please skip this section if you are using a different database or already have a supported database server running elsewhere.

Install MySQL server:

```bash
sudo apt-get install mysql-server mysql-client

# When prompted, provide a password for the root user to access the MySQL server.
```

Below we'll create a `stackdio` database and grant permissions to the `stackdio` user for that database.

> **WARNING**: we're not focusing on security here, so the default MySQL setup definitely needs to be tweaked, passwords changed, etc., but for a quick-start guide this is out of scope. Please, don't run this as-is in production :)

```bash
echo "create database stackdio; \
grant all on stackdio.* to stackdio@'localhost' identified by 'password';" | \
mysql -hlocalhost -uroot -ppassword
```

### virtualenvwrapper

```bash
# install the package
sudo apt-get install virtualenvwrapper

# post-install step for virtualenvwrapper shortcuts
source /etc/bash_completion.d/virtualenvwrapper
```

### Core requirements

* gcc and other development tools
* git
* mysql-devel
* swig
* python-devel
* rabbitmq-server

To quickly get up and running, you can run the following to install the required packages.

```bash
# Install requirements needed to install stackd.io
sudo apt-get install python-dev libssl-dev libncurses5-dev swig \
    libmysqlclient-dev rabbitmq-server git nginx
```

# Next Steps

You're now finished with the Ubuntu-specific requirements for stackd.io. You can head back over to the [Quick Start Guide](quickstart.md) and continue the installation of stackd.io.

