/usr/bin/python2
# coding=utf-8

"""Update the Zotero lab library with PMID/PMCID info from the EndNote
   export file.

   Todo:
   - make sure it gets pub #288 (markley 2012) right
   - run as cronjob
   - add any new pubs from pub page to library
   - existing pubs
     - check for changes (renumber if necesary; use pmid or other unique id)
     - compare against pubmed
     - fix authors if necessary (e.g. Forster), add pmcid etc.
"""

from pyzotero import zotero

def read_endnote():
    def process_entry(entry, m):
        if entry:
            if entry['call'] in m:
                raise ValueError("Duplicate call number %s" % entry['call'])
            m[entry['call']] = entry

    m = {}
    entry = {}
    for line in open('SaliMaster.entxt'):
        if line.startswith('%0') or len(line.rstrip('\r\n\t ')) == 0:
            process_entry(entry, m)
            entry = {}
        elif line.startswith('%L'):
            entry['call'] = int(line.rstrip('\r\n').split()[1])
        elif line.startswith('%M'):
            i = line.rstrip('\r\n').split()[1]
            if not i.startswith('WOS:'):
                entry['pmid'] = int(i.split(';')[0])
        elif line.startswith('%2'):
            i = line.rstrip('\r\n').split(' ', 1)[1]
            i = i.replace('PMCID', '')
            if 'TBD by Journal' in i:
                entry['pmcid'] = i.strip()
            else:
                entry['pmcid'] = int(i)
    process_entry(entry, m)
    return m

def get_extra_for_call(call, pmid_map):
    try:
        call = int(call)
    except ValueError:
        return None
    if call in pmid_map:
        v = pmid_map[call]
        extra = ''
        if 'pmid' in v:
            extra += "PMID: %d" % v['pmid']
        if 'pmcid' in v:
            if isinstance(v['pmcid'], int):
                extra += "\nPMCID: PMC%d" % v['pmcid']
            else:
                extra += "\nPMCID: %s" % v['pmcid']
        return extra

pmid_map = read_endnote()

zot = zotero.Zotero(ADD_AUTH_HERE)
num_items = zot.num_items()
for i in range(0, num_items, 10):
    print "Checking items %d-%d of %d" % (i+1, min(i+10, num_items), num_items)
    for item in zot.top(start=i+1, limit=10):
        modified = False
        call = item['data']['callNumber']
        for author in item['data']['creators']:
            if author['lastName'] == 'Forster':
                print "Fixing Frido's name in call %s" % call
                author['lastName'] = 'Förster'
                modified = True
        extra = get_extra_for_call(call, pmid_map)
        if extra and item['data']['extra'] != extra:
            print "Updating call %s with extra %s" % (call, extra)
            item['data']['extra'] = extra
            modified = True
        if modified:
            zot.update_item(item)
