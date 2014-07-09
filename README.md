mugsy
======

Mugsy is a file integrity monitor.

It runs as a daemon and any file modifications made to your system are logged locally and also sent to an [elasticsearch](http://www.elasticsearch.org) server.  That means you can use [kibana](http://www.elasticsearch.org/overview/kibana/) as a sweet dashboard to monitor what is changing on your servers, or easily roll your own reports.

#### Install

(rpm is forthcoming.  Just need to find a public yum repo to serve it from)

```
sudo yum install mugsy
```

#### Setup and run

Copy the example config:

```
sudo cp /var/mugsy/config.yml.example /var/mugsy/config.yml
```

At a minimum, you'll need to change the elasticsearch host/port.


Start the daemon:

```
sudo service mugsy start
```

#### Example config.yml

```
# Elasticsearch server
es_host: eshost.example.com
es_port: 9200

# Logs
logdir: /var/mugsy/logs
loglevel: info

# directories to monitor
# note: no single file paths, only specify directories here
path_list:
- /boot
- /lib
- /lib64
- /sys
- /bin
- /sbin
- /usr/bin
- /usr/sbin
- /usr/local/bin
- /usr/local/etc
- /usr/local/sbin
- /etc

# patterns to ignore
ignore_list:
- /etc/mtab*
- /sys/devices*
- /etc/prelink.cache*
- "*.swpx"
- "*.swp"
- "*.swx"
- "*.git*"
- "*.svn*"
- "*.svn/*"
- /etc/pki/nssdb/key*
- /etc/pki/nssdb/cert*
```

#### Logs

/var/mugsy/logs is the default location, but the log directory can be configured in config.yml.

#### Notes

- inotify is used to detect real-time file changes via [py watchdog](https://pypi.python.org/pypi/watchdog)
- Mugsy is a stand-alone executable.  Your system does not need to have python installed for it to run, thanks to [cx_freeze](http://cx-freeze.sourceforge.net/).  So theoretically, mugsy could be built for cross-platform use.
- The list of directories to monitor in the example config should not be considered complete from a security perspective.  You really should monitor ALL directories on your system.   That can get pretty noisy, so the default list is my attempt at a list of important directories to monitor.   I hope that the community can help build a standard list of "important directories to monitor for changes on linux systems".  Please submit an issue with any suggestions.

#### Contributing
Pull requests, bug reports, and feature requests are encouraged.


#### Install via github

Mugsy is built and tested on CentOS/RHEL 6.  You can also run mugsy in virtualenv or build it for your environment.


Clone and setup virtualenv:

```
git clone git@github.com:imsweb/mugsy.git
virtualenv --no-site-packages mugsy
cd mugsy && source bin/activate
pip install -r requirements.txt
```

After that you can run the daemon from the virtualenv:

```
python mugsy.py start
```

building the binary for your system:

```
python setup.py install
sudo mkdir -p /var/mugsy
sudo cp -r build/exe.linux-x86_64-2.6 /var/mugsy/lib    # path varies with kernel version
# start it!
/var/mugsy/lib/mugsy start
```
