#!/usr/bin/env python
from os.path import isfile, join
from os import walk
import urllib2, urllib, json, sys
from alacollectory import Collectory 
from DwcaInfo import DwcaInfo


print "start loading datasets"

mypath = "/var/www/datasets/"
collectory_path = "http://172.16.16.86/collectory"
api_key = "inbio_test"
datasets_url = "http://172.20.60.64/datasets/"

for root, dirs, files in walk(mypath):
    for file in files:
        if isfile(join(mypath,file)):
            datasetkey = file[:-4]
            print datasetkey

            # get dataset info from gbif
            response = urllib2.urlopen("http://api.gbif.org/v1/dataset/" + datasetkey)
            dataset_string = response.read()

            # dataset json encode
            dataset_json = json.loads(dataset_string)
            print "Organization Key: " + dataset_json['publishingOrganizationKey']

            # get organization info
            response = urllib2.urlopen("http://api.gbif.org/v1/organization/" + dataset_json['publishingOrganizationKey'])
            organization_string = response.read()
            organization_json = json.loads(organization_string)
            print "Organization: " + organization_json['title']

            collectory = Collectory(collectory_path)

            # send dataset to server
            result = collectory.uploadDataResource("{0}{1}.zip".format(datasets_url, datasetkey))
            if (not result['success'] ):
                print "Error loading dataset " + datasetkey
                continue

            dataResourceUid = result['dataResourceUid']

            # create / update institution
            institution = Collectory.gbifOrganizationToAlaInstitution( organization_json)
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

            # recover dataResource and Institution 
            dataResourceCollectory = collectory.search('dataResource', 
                                                    {'uid': result['dataResourceUid']})

            # create / update collection
            collectionCollectory = collectory.search('collection',
                                                    {'guid': institution['guid']})
            if len(collectionCollectory) == 0:
                collection = {}
                collection['name'] = dataResourceCollectory['name']
                collection['institution'] = institutionCollectory
                collection['guid'] = institution['guid']
                print collection
                collectory.createUpdate('collection', collection)
                collectionCollectory = collectory.search('collection',
                                                    {'guid': institution['guid']})

            # provider codes
            dwcaInfo = DwcaInfo.getDwcaInfo (join(mypath,file))

            collectory.createProviderCode (dwcaInfo.institutionCode)
            collectory.createProviderCode (dwcaInfo.collectionCode)
            


