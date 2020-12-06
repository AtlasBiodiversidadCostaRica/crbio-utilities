#!/usr/bin/env python
from os.path import isfile, join
from os import walk
import urllib2, urllib, json, sys
from alacollectory import Collectory 
from DwcaInfo import DwcaInfo
import re

reload(sys)  
sys.setdefaultencoding('utf8')

print "start loading datasets"

#mypath = "/var/www/datasets/"
mypath = "/srv/datos.biodiversidad.go.cr/www/html/datasets/"
collectory_path = "http://datos.biodiversidad.go.cr/collectory/"

#api_key = "inbio_test"
api_key = "dummy-registry-api-key"
#datasets_url = "http://10.0.2.184/datasets/"
datasets_url = "http://datos.biodiversidad.go.cr/datasets/"


for root, dirs, files in walk(mypath):
    for file in files:
        if isfile(join(mypath,file)):
            datasetkey = file[:-4]
            print datasetkey

            # get dataset info from gbif
            response = urllib2.urlopen("http://api.gbif.org/v1/dataset/" + datasetkey)
            dataset_string = response.read().encode("utf-8")

            # dataset json encode
            dataset_json = json.loads(dataset_string)
            print "Organization Key: " + dataset_json['publishingOrganizationKey']

            # get organization info
            response = urllib2.urlopen("http://api.gbif.org/v1/organization/" + dataset_json['publishingOrganizationKey'])
            organization_string = response.read().encode("utf-8")
            organization_json = json.loads(organization_string)
            print "Organization:{}".format(organization_json['title'].encode("utf-8"))


            collectory = Collectory(collectory_path)

            # send dataset to server
            result = collectory.uploadDataResource("{0}{1}.zip".format(datasets_url, datasetkey))
            if (not result['success'] ):
                print "Error loading dataset " + datasetkey
                continue

            dataResourceUid = result['dataResourceUid']

            # create / update institution
            institution = Collectory.gbifOrganizationToAlaInstitution( organization_json)
#            print institution
#            continue
            institutionCollectory = collectory.search('institution', 
                                                    {'guid': institution['guid']})
            if len(institutionCollectory) == 0:
                institution['api_key'] = api_key
                institution['user'] = "python"
                print collectory.createUpdateInstitution(institution)
                # retrieve again to obtain the uid
                institutionCollectory = collectory.search('institution', 
                                                    {'guid': institution['guid']})

            institutionCollectory = institutionCollectory[0]
            print institution

            # recover dataResource and Institution 
            dataResourceCollectory = collectory.search('dataResource', 
                                                    {'uid': result['dataResourceUid']})

            # create / update collection
            collectionCollectory = collectory.search('collection',
                                                    {'guid': datasetkey})
            if len(collectionCollectory) == 0:
                collection = {}
                collection['name'] = dataResourceCollectory['name']
                collection['institution'] = institutionCollectory
                collection['guid'] = datasetkey 
                if 'latitude' in institution:
                    collection['latitude'] = institution['latitude']
                if 'longitude' in institution:
                    collection['longitude'] = institution['longitude']
                collection['isALAPartner'] = 'on'
                print collection
                collectory.createUpdate('collection', collection)
                collectionCollectory = collectory.search('collection',
                                                    {'guid': datasetkey})

            collectionCollectory = collectionCollectory[0]

            # add collection to data resource consumer
            collectory.addConsumerCollection(dataResourceUid,
                                             collectionCollectory['uid'])

            # provider codes
            dwcaInfo = DwcaInfo.getDwcaInfo (join(mypath,file))
            
            collectionId = re.search('[0-9]+',collectionCollectory['uid']).group(0)
            collectory.createProviderMap(collectionId,
                                         dwcaInfo.institution_collection_codes.iteritems())




