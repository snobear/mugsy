import subprocess
import sys
import os
import socket
import time
import logging
import stat
import yaml
from daemon import runner
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import hashlib
from elasticsearch import Elasticsearch

# log level config options and corresponding logging level object
loglevel = { 
  'critical' : logging.CRITICAL,
  'error'    : logging.ERROR,
  'warning'  : logging.WARNING,
  'info'     : logging.INFO,
  'debug'    : logging.DEBUG,
}

# special mappings used when creating the index
mapping = {
  "mappings" : {
    "filemeta" : {
      "properties" : {
        "dirpath" : {
          "type" : "string",
          "index" : "not_analyzed",
          "omit_norms" : True,
          "index_options" : "docs"
        },
        "filepath" : {
          "type" : "string",
          "index" : "not_analyzed",
          "omit_norms" : True,
          "index_options" : "docs"
        },
      }
    }
  }
}

'''
Handler for each file change event
'''
class CustomHandler(PatternMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        super(CustomHandler, self).__init__(*args, **kwargs)

        # Elasticsearch init
        try:
            self.es = Elasticsearch(hosts={config['es_host'] : config['es_port'] })
        except Exception, e:
            applog.exception("Error creating elasticsearch connection: %s" % e)
            sys.exit(1)

    '''
    Get a specified field for a given file via stat command
    See `man stat` for full list of formatting options to use for statfield
    '''
    def filestat(self, event, statfield):
        # get file's new path if it was moved
        if event.event_type == 'moved':
            filepath = event.dest_path
        else:
            filepath = event.src_path

        # vi creates temp tilde files.  strip the tilde if so.
        if filepath.endswith('~'):
            filepath = filepath[:-1]

        p = subprocess.Popen(['/usr/bin/stat', '--format', statfield, filepath], stdout=subprocess.PIPE)

        output, err = p.communicate()
        if err:
            applog.info("Error in stat command subprocess: %s") % err
            result = None
        else:
            result = output.split('\n')[0]
        
        # remove the line break that gets added from the subprocess command
        return result
    
    def process(self, event):
        '''
        event.event_type 
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        '''

        if event.is_directory:
            directory = event.src_path
        else:
            directory = os.path.dirname(event.src_path)

        # build dictionary of data about this event to store in Elasticsearch
        doc = {
            'file': event.src_path,
            'timestamp': datetime.now(),
            'event': event.event_type,
            'hostname': socket.gethostname(),
            'directory': directory,
            # two fields are used here because elasticsearch "analyzes" and splits strings
            # by default. see https://github.com/elasticsearch/kibana/issues/190
            'file': event.src_path,
            'filepath': event.src_path,
            'directory': directory,
            'dirpath': directory,
        }

        # make sure file exists before attempting stat command
        # open issue: https://github.com/gorakhargosh/watchdog/issues/205        
        if event.event_type != 'deleted' and (os.path.exists(event.src_path)):

            # get file stats
            fstats = self.filestat(event, "%a, %A, %F, %G, %g, %i, %U, %u, %x, %y, %z, %s")
            fstats = fstats.split(',')

            doc['perms_octal'] = fstats[0]
            doc['perms_human'] = fstats[1]
            doc['file_type'] = fstats[2]
            doc['group'] = fstats[3]
            doc['gid'] = fstats[4]
            doc['inode_num'] = fstats[5]
            doc['user'] = fstats[6]
            doc['uid'] = fstats[7]
            doc['last_access_time'] = fstats[8]
            doc['last_mod_time'] = fstats[9]
            doc['last_change_time'] = fstats[10]
            doc['size_bytes'] = fstats[11]

            if event.event_type == 'moved':
                doc['dest_path'] = event.dest_path

        # send to ES
        self.log_event(doc)

    def on_any_event(self, event):
        self.process(event)

    '''
    Log the event
    Send to Elasticsearch and local log
    ''' 
    def log_event(self, doc):
        # log locally
        eventlog.info("event: %s" % doc)
        applog.info("event being logged...")

        # send to ES
        try:
            index_name = "mugsy-%s" % datetime.now().strftime('%Y.%m.%d')

            cr = self.es.indices.create(index=index_name, body=mapping, ignore=400)
            try:
                res = self.es.index(index=index_name, doc_type='filemeta', body=doc)
                applog.debug("log sent to elasticsearch. result : %s" % res)
            except Exception, e:
                applog.exception("error sending to elasticsearch server: %s" % e)
        except Exception, e:
            applog.exception("Error creating elasticsearch index: %s" % e)

'''
Main
'''
class Mugsy():
    def __init__(self, **kwargs):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path =  '/var/run/mugsy.pid'
        self.pidfile_timeout = 5
        self.startup_checks()

    def startup_checks(self):
        # enforce strict permissions for main directory
        os.chmod('/var/mugsy', 0700)

        # create logs directory if doesn't exist
        if not os.path.exists(config['logdir']):
            os.makedirs(config['logdir'])

    def run(self):
        applog.info("Mugsy is starting...")

        ''' 
        Watchdog/inotify event handler
        '''
        applog.info("Ignoring paths containing these patterns: %s" % config['ignore_list'])
        event_handler = CustomHandler(ignore_patterns = config['ignore_list'])

        # set up a watcher for each path in our list of paths
        for p in config['path_list']:
            if os.path.exists(p):
                path = str(p)
                observer = Observer()
                observer.schedule(event_handler, path, recursive=True)
                observer.start()
                applog.info("Monitor started for path %s" % p)
            else:
                applog.info("Skipping %s.  Directory does not exist." % p)

        applog.info("All monitors have been started.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            applog.exception('KeyboardInterrupt caught')
            observer.stop()
        except Exception, e:
            applog.exception(e)

        observer.join()

if __name__ == "__main__":

    # load config
    if getattr(sys, 'frozen', False):
        # frozen (mugsy is being run from a stand-alone binary)
        app_dir = "%s/.." % os.path.dirname(sys.executable)
    else:
        # unfrozen (being run as a py script)
        app_dir = os.path.dirname(os.path.realpath(__file__))

    app_config_file = "%s/config.yml" % app_dir

    try:
        config = yaml.load(file(app_config_file))
    except IOError:
        sys.exit("config.yml does not exist.  You can copy config.yml.example to config.yml and customize it.")

    app = Mugsy()

    '''
    Set up logging
    '''
    applog_file = "%s/app.log" % config['logdir']
    eventlog_file = "%s/event.log" % config['logdir']
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    lvl = loglevel[config['loglevel'].lower()]

    # Application logs
    applog = logging.getLogger('app')
    ah = logging.FileHandler(applog_file)
    ah.setFormatter(log_format)
    applog.addHandler(ah)
    applog.setLevel(lvl)

    # File event logs, for logging locally
    eventlog = logging.getLogger('events')
    eh = logging.FileHandler(eventlog_file)
    eh.setFormatter(log_format)
    eventlog.addHandler(eh)
    eventlog.setLevel(lvl)
    
    # set logging handler for elasticsearch module
    eslog = logging.getLogger('elasticsearch')
    eslog.addHandler(eh)
    eslog.setLevel(lvl)

    '''
    Start daemon
    '''
    daemon_runner = runner.DaemonRunner(app)
    # This ensures that the logger file handle does not get closed during daemonization
    daemon_runner.daemon_context.files_preserve=[ah.stream, eh.stream]
    daemon_runner.do_action()

