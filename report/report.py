#!/usr/local/bin/python2.7
# Send a summary report of file changes
#
from elasticsearch import Elasticsearch, NotFoundError
from pprint import pprint
import queries
import os
import sys
import operator
import yaml
from datetime import date, timedelta
import json
import logging
from collections import defaultdict
import re

"""
Settings
"""
esindex_prefix = 'mugsy-'
dashboard_url = ''  # e.g. kibana URL
mail_to = "root"
mail_from = "mugsy"
mail_subject = "[mugsy] File Integrity Report"

# substrings to strip out (regex)
# allows us to collapse similar filenames
# use this awesome tool to build them: http://regexpal.com
regex_remove = [
    "\d{8}-\d+-\w+(?:-\w+)?",
    ";\w+$",
    "sudo(?:.augnew)?.\w+$",
    ".puppettmp_\d{4}$",
    ".#prelink#.\w+$",
    "(:?iptables|cacerts|ca-bundle.trust.crt).\w{6}$",
    "(:?passwd|group|shadow).\d{5}$",
]

# only search yesterday and today's elasticsearch indicies
# more efficient than searching all of them
yesterday = (date.today() - timedelta(1)).strftime('%Y.%m.%d')
today = date.today().strftime('%Y.%m.%d')
esindex = "%s%s,%s%s" % (esindex_prefix, yesterday, esindex_prefix, today)

# logging
logging.basicConfig()

# load mugsy config
#
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
    sys.exit("config file %s does not exist.  You can copy config.yml.example to config.yml and customize it." % app_config_file)

thisdir = os.path.dirname(__file__)
template_path = os.path.join(thisdir, 'report.html')

# prepare and send email
def send_email(output, host_output):
    import string
    import smtplib
    from email.mime.text import MIMEText

    # build the email
    data_header = "{0:>5} {1:<10}".format('Count', 'File')

    email_body = """Report period: %s to %s
    
Dashboard: %s

========================
File changes, all hosts:
========================
%s

========================
File changes per host:
========================
%s
    """ % (yesterday, today, dashboard_url, output, host_output)

    msg = MIMEText(email_body)
    msg['Subject'] = mail_subject
    msg['From'] = mail_from
    msg['To'] = mail_to
    s = smtplib.SMTP('localhost')
    s.sendmail(mail_from, [mail_to], msg.as_string())
    s.quit()


# This will return a list with similar strings removed
# It works pretty well, but it is relatively aggressive with
# removing strings that we may want to see in our File Integrity report.
# ended up using the "maintain a list of patterns to remove" approach.
#
import difflib 
def similarity(L_1, L_2):
    L_1 = set(intern(w) for w in L_1)
    L_2 = set(intern(w) for w in L_2)
    #pprint(L_1)

    for w in L_1:
        matches = difflib.get_close_matches(w, L_2)
        if len(matches):
            L_1 = L_1 - set(matches)
            L_2 = L_2 - set(matches)
            # put the "original" value back in
            L_2.add(w)
    return L_2

if __name__ == "__main__":
    # initialize
    rdata = {}
    rdata['host_counts'] = ""
    rdata['file_counts'] = ""
    rdata['total'] = 0
    files = list()

    # Elasticsearch init
    try:
        if ('http_user' in config) and ('http_pass' in config):
            es = Elasticsearch(hosts=config['es_hosts'],
                                    http_auth="%s:%s" % (config['http_user'],config['http_pass'])
                                    )
        else:
            es = Elasticsearch(hosts=config['es_hosts'])
    except Exception, e:
        exception("Error creating elasticsearch connection: %s" % e)
        sys.exit(1)

    """
    File change list
    """
    # ignore_unavailable means we don't care if one or more indexes we're searching on don't exist.
    # typically means today's index hasn't been created because no events have occurred yet.
    result = es.search(body=queries.file_changes, index=esindex, ignore_unavailable=True)
    result_buckets = result['aggregations']['mugsy']['buckets']

    filelist = defaultdict(set)
    for bucket in result_buckets:
        directory = json.dumps(bucket['files']['hits']['hits'][0]['_source']['directory'])[1:-1]

        # the [1:-1] will remove the leading and trailing double quotes
        filepath = json.dumps(bucket['files']['hits']['hits'][0]['_source']['filepath'])[1:-1]
        basename = os.path.basename(filepath)

        for regexstr in regex_remove:
            basename = re.sub(regexstr, "", basename)

        # directory names ending in .lock will be ignored from this report
        if (directory[-5:] != '.lock') and (basename != ''):
            filelist[directory].add(basename)

    sorted_filelist = sorted(filelist)
    curr_dir = None
    out = ""
    for directory in sorted_filelist:
        if len(filelist[directory]) <= 1:
            single_file = True
        else:
            single_file = False
        # add directory name to output
        if (curr_dir is None) or (curr_dir != directory):
            curr_dir = directory
            if single_file:
                out +=  "%s/" % curr_dir
            else:
                out +=  "%s/\n" % curr_dir

        # loop through files in this directory and add to output
        for f in filelist[directory]:
            if single_file:
                out += "%s\n" % f
            else:
                out += "|- %s\n" % f

    """
    Host frequencies
    """
    # list of all hosts for sanity check
    result = es.search(body=queries.all_hosts_listing, index="%s*" % esindex_prefix, ignore_unavailable=True)
    all_hosts = result['aggregations']['hosts']['buckets']

    # host frequencies
    result = es.search(body=queries.hosts_freq, index=esindex, ignore_unavailable=True)
    hosts  = result['aggregations']['hosts']['buckets']

    # merge results
    for h in all_hosts:
        if not any(d['key'] == h['key'] for d in hosts):
            # host is not in our results, so add it as 0 for sanity check purposes
            h['doc_count'] = 0
            hosts.append(h)

    sorted_hosts = sorted(hosts, key=operator.itemgetter('doc_count'), reverse=True)

    total_hosts = 0
    hosts_output = "{0:>6}: {1:<20}\n".format("Count","Hostname")
    for host in hosts:
        total_hosts += 1
        # strip domain name
        hostname = host['key'].split('.')[0]
        hosts_output += "{0:>6}: {1:<20}\n".format(host['doc_count'], hostname)

    hosts_output += "Total hosts reporting in: %d" % total_hosts

    """
    Create and send the email!
    """
    send_email(out, hosts_output)

