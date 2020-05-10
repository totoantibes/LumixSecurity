#!/usr/bin/env python

import http.client, urllib.request, urllib.parse, urllib.error, xml.dom.minidom, pickle, os, sys, time

def get_num_pics(cam_ip):
    while [1]: 
        try :
            r = urllib.request.urlopen('http://%s/cam.cgi?mode=get_content_info' % cam_ip)
        except :
            print('error in get num pics')
            time.sleep(1)
        else :
            break 
    x = xml.dom.minidom.parseString(r.read())
    num_pics = int(x.getElementsByTagName('total_content_number')[0].firstChild.nodeValue)
    r.close()
    
    print('num_pics = %d' % num_pics)
    return num_pics

def get_pics(cam_ip, downloaded={}):
    print('getting pics')
    while [1]:
        try : 
            #urllib.request.urlretrieve('http://%s/cam.cgi?mode=stopstream&value=0' % cam_ip, 'D:\\lumixsecurity\\buffer')
            urllib.request.urlretrieve('http://%s/cam.cgi?mode=camcmd&value=playmode' % cam_ip, 'D:\\lumixsecurity\\buffer2')
        except :
            time.sleep(1)
        else :
            break
    num_pics = get_num_pics(cam_ip)
    page_size = 15
    #start = max (0,num_pics - page_size)
    start =0
    if 'start' in downloaded: start = downloaded['start']
    if num_pics < start: start = 0 # likely user formatted/cleared card
    while start < num_pics:
        num_to_download =min ( page_size,  num_pics - start )
        soap_connection = http.client.HTTPConnection(cam_ip, 60606)
        soap_data = '''<?xml version="1.0" encoding="utf-8"?>
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
    <u:Browse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1" xmlns:pana="urn:schemas-panasonic-com:pana">
    <ObjectID>0</ObjectID>
    <BrowseFlag>BrowseDirectChildren</BrowseFlag>
    <Filter>*</Filter>
    <StartingIndex>%d</StartingIndex>
    <RequestedCount>%d</RequestedCount>
    <SortCriteria></SortCriteria>
    <pana:X_FromCP>LumixLink2.0</pana:X_FromCP>
    </u:Browse>
    </s:Body>
    </s:Envelope>
    ''' % (start, num_to_download)
        soap_headers = {
            'Content-Type': 'text/xml; charset="UTF-8"',
            'Content-Length': len(soap_data),
            'SOAPACTION': 'urn:schemas-upnp-org:service:ContentDirectory:1#Browse',
        }
        soap_connection.request('POST', '/Server0/CDS_control', soap_data, soap_headers)
        try : 
            r = soap_connection.getresponse()
            x = xml.dom.minidom.parseString(r.read())
            for res in xml.dom.minidom.parseString(x.getElementsByTagName('Result')[0].firstChild.nodeValue).getElementsByTagName('res'):
                if 'DLNA.ORG_PN=JPEG_LRG' not in res.getAttribute('protocolInfo'): continue
                u = res.firstChild.nodeValue
                l = u[u.rindex('/') + 1:]
                if l in downloaded:
                    print("already have %s, skipping" ,l)
                    downloaded[l] = True
                    start +=1 
                    downloaded['start'] = start
                    continue
                print("downloading %s", l)
                try :
                    urllib.request.urlretrieve(u, 'D:\\lumixsecurity\\'+l)
                except :
                    print ('error reading image %s skipping', l)
                downloaded[l] = True
            start +=1 
            downloaded['start'] = start
        except :
            print( "error reading from camera")
            urllib.request.urlretrieve('http://%s/cam.cgi?mode=camcmd&value=playmode' % cam_ip, 'D:\\lumixsecurity\\buffer2')
    return downloaded

def get_new_pics(cam_ip, state_fn=None):
    if not state_fn: state_fn = 'D:\\lumixsecurity\\.gh4'
    try:
        f = open(state_fn, 'rb')
        downloaded = pickle.load(f)
        f.close()
    except: downloaded = {}
    downloaded = get_pics(cam_ip, downloaded)
    f = open(state_fn, 'wb')
    pickle.dump(downloaded, f)
    f.close()
