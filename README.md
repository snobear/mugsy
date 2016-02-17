mugsy
======

Mugsy is a Linux file integrity monitor.

It runs as a daemon and any file modifications made to your system on directories you've specify to monitor are logged locally and optionally sent to your [elasticsearch](http://www.elasticsearch.org) server(s).

If you have mugsy ship your file changes to elasticsearch, you can then easily generate reports with a script (see report/ directory for example report script) or a dashboard such as [kibana](http://www.elasticsearch.org/overview/kibana/).

#### Install


Install the latest [release](https://github.com/imsweb/mugsy/releases):

```
sudo yum install https://github.com/imsweb/mugsy/releases/download/1.0.1/mugsy-1.0.1-1.x86_64.rpm
```

#### Setup and run

Copy the example config:

```
sudo cp /var/mugsy/config.yml.example /var/mugsy/config.yml
```

At a minimum, you'll need to change the elasticsearch host settings.


Start the daemon:

```
sudo service mugsy start
```

#### Example config.yml

```
# Elasticsearch servers
# format is host: port
# add a line for each host in your cluster
es_logging: true
es_hosts:
  examplehost01: 9200
  examplehost02: 9200

# basic http auth (optional)
#http_user: myuser
#http_pass: mypassword

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
- "*.svn*"
```

#### Reports

***Daily Email report***

Download the `report.py` and `queries.py` scripts found in `report/` in this repo and save to /var/mugsy. Then set up a cron job to fire off a daily report:

```
# Daily file integrity report [mugsy]
0 7 * * * /var/mugsy/report.py > /dev/null
```

Note the daily file integrity email report requires that you are having mugsy ship your logs to elasticsearch.

Of course you can roll your own using the many elasticsearch client libraries or use Kibana as a dashboard to search and visualize.

Example daily report:

```
Report period: 2016.02.16 to 2016.02.17
    
========================
File changes, all hosts:
========================
/etc/
|- passwd
|- hosts
|- ntp.conf
/etc/foo/foo.conf
/usr/bin/firefox

========================
File changes per host:
========================
 Count: Hostname            
    16: es-01        
    12: es-02        
    11: webapp-02               
    11: test04        
    10: db20          
    10: mw03               
    10: mw04               
     7: webapp-03        
     6: db04
     6: somehost05
Total hosts reporting in: 10
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
