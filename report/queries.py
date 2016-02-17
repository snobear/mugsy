import datetime
now = datetime.datetime.now()

hours_ago = now - datetime.timedelta(hours=24)
month_ago = now - datetime.timedelta(days=31)

# number of files to truncate report at
max_files_in_report = 2000

# query.  you can filter out strings here.
querystr = """
NOT *puppettmp*
AND NOT (filepath:*passwd.* OR filepath:*shadow.* OR filepath:*group.*)
AND NOT filepath:*.svn*
AND NOT filepath:*.git*
AND NOT filepath:"/etc/opt/mx/config/.lmlastupdate"
AND NOT filepath:"/etc/aliases.db"
AND NOT file_type:"directory"
"""

file_freq = {
  "facets": {
    "terms": {
      "terms": {
        "field": "filepath",
        "size": max_files_in_report,
        "order": "count",
        "exclude": []
      },
      "facet_filter": {
        "fquery": {
          "query": {
            "filtered": {
              "query": {
                "bool": {
                  "should": [
                    {
                      "query_string": {
                        "query": querystr
                      }
                    }
                  ]
                }
              },
              "filter": {
                "bool": {
                  "must": [
                    {
                      "range": {
                        "timestamp": {
                          "from": hours_ago,
                          "to": "now"
                        }
                      }
                    }
                  ]
                }
              }
            }
          }
        }
      }
    }
  },
  "size": max_files_in_report
}

file_changes={
  "query" : {
    "bool": {
      "must_not": { "match": { "file_type": "directory"  }},
    }
  },
  "aggs": {
      "mugsy" : {
        "terms":{
          "field": "filepath",
          "size": 2000
         },

         "aggs":{
           "files":{
             "top_hits":{
               "size":1
             }
           }
        }
      }
    },
}

hosts_freq={
  "size": 0,
  "aggs": {
    "hosts": {
      "terms": {
        "field": "hostname",
        "size": 0,
        "order": {
          "_count": "desc"
        }
      }
    }
  },
  "query": {
    "filtered": {
      "query": {
        "query_string": {
          "analyze_wildcard": True,
          "query": querystr
        }
      },
      "filter": {
        "bool": {
          "must": [
            {
              "range": {
                "timestamp": {
                  "gte": hours_ago,
                  "lte": now
                }
              }
            }
          ],
          "must_not": []
        }
      }
    }
  },
}


all_hosts_listing={
  "size": 0,
  "aggs": {
    "hosts": {
      "terms": {
        "field": "hostname",
        "size": 0,
        "order": {
          "_count": "desc"
        }
      }
    }
  },
  "query": {
    "filtered": {
      "query": {
        "query_string": {
          "analyze_wildcard": True,
          "query": "*"
        }
      }
    }
  },
}
