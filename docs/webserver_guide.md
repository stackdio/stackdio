# stackd.io webserver guide

This guide will help you quickly get the web portion of stackd.io running behind either Apache or Nginx. You should've already worked through the [quickstart guide](quickstart.md) before running through the steps below. As with the quickstart, our focus is not entirely on building out a production-ready system, but merely helping you quickly get a system stood up to become familiar with stackd.io. Once you understand how it works, then we can start hardening the system for production use.

So, with that said, there are two paths to take: Apache or Nginx. We recommend using whichever you feel more comfortable with. Some of us here like Apache, while others like Nginx. Your mileage may vary :)

# Apache

### CentOS Installation

Install required packages:

```bash
sudo yum install httpd mod_wsgi mod_ssl
```

Followed by having stackd.io generate a simple Apache configuration file for serving up the Django-based API and static assets and store the output into the appropriate location.

```bash
stackdio config apache | sudo tee /etc/httpd/conf.d/stackdio.conf > /dev/null
```

> NOTE: You may pass --with-ssl to generate boilerplate for serving over SSL, but you will need to add your certs and point to them in the configuration file.

And that's it...let's start the server and then point your browser to the hostname on port 80 (use https if you decided to serve over SSL.)

```bash
sudo service httpd start
```

### Ubuntu Installation

Install required packages:

```bash
sudo apt-get install apache2 libapache2-mod-wsgi
```

and just like the CentOS instructions, generate and store the Apache configuration file into the correct location:

```bash
stackdio config apache | sudo tee /etc/apache2/sites-enabled/stackdio.conf > /dev/null
```

> NOTE: You may pass --with-ssl to generate boilerplate for serving over SSL, but you will need to add your certs and point to them in the configuration file.

And that's it...let's start the server and then point your browser to the hostname on port 80 (use https if you decided to serve over SSL.)

# Nginx

### CentOS Installation

### Ubuntu Installation
