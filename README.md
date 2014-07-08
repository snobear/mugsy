mugsy
======

Mugsy is a file integrity monitor.  

It runs as a daemon and any file modifications made to your system are logged locally and also sent to an [elasticsearch](http://www.elasticsearch.org) server.  That means you can use [kibana](http://www.elasticsearch.org/overview/kibana/) as a sweet dashboard to monitor what is changing on your servers, or easily roll your own reports.

#### Install

```
yum install mugsy
```

#### Setup and run

Mugsy ships with an example config that should have some sane defaults as far as what directories should be monitored and ignored.

```
sudo cp /var/mugsy/config.yml.example /var/mugsy/config.yml

# at a minimum, you'll need to change es_host and es_port to your ES host/port.
sudo vim /var/mugsy/config.yml

# start the daemon
sudo service mugsy start
```

#### Install via github

```
git clone git@github.com:imsweb/mugsy.git
virtualenv --no-site-packages mugsy
cd mugsy && source bin/activate
pip install -r requirements.txt
python mugsy.py start
```


#### Logs

/var/mugsy/logs is the default location, but the log directory can be configured in config.yml.

#### Notes

- inotify is used to detect real-time file changes via [py watchdog](https://pypi.python.org/pypi/watchdog)
- The list of directories to monitor in the example config should not be considered complete from a security perspective.  You should monitor ALL directories on your system, but this can get noisy.  Please submit an issue to suggest any changes to the default list.
- Mugsy is a stand-alone executable.  Your system does not need to have python installed for it to run, thanks to [cx_freeze](http://cx-freeze.sourceforge.net/).  So theoretically, mugsy could be built for cross-platform use.

#### Contributing
Pull requests, bug reports, and feature requests are encouraged.
