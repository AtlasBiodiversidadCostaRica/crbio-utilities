#!/usr/bin/env python
"""
simple tool to access service from Ala generic-collectory project https://github.com/AtlasOfLivingAustralia/generic-collectory
"""

import sys
import urllib2 
import urllib
import json
import unittest
import re

class Collectory(object):

    def __init__(self, url):
        self.collectoryUrl = url

    def createUpdateInstitution(self, institution):
        print "createUpdateInstitution"
        response = self.createUpdate('institution', institution)
        print response.read()

    def createUpdate(self, entity, data):
        print "createUpdate {}".format(entity)
        data_string = json.dumps(data)
        response = self.collectoryPost(
                        "{0}/ws/{1}/".format(self.collectoryUrl, entity),
                        data_string)
        return response

    def uploadDataResource(self, url):
        print "uploadDataResource"
        path = "{0}/dataResource/downloadGBIFFile/?url={1}".format(self.collectoryUrl, url)
        response = self.collectoryGet(path)
        result = response.read()
        return json.loads(result)

    def lookup(self, institutionCode, collectionCode):
        institutionCode = urllib2.quote(institutionCode)
        collectionCode  = urllib2.quote(collectionCode)
        # fix apache %2F transforme to /
        institutionCode  = institutionCode.replace('/','%252F')
        collectionCode  = collectionCode.replace('/','%252F')

        path = "{0}/ws/lookup/inst/{1}/coll/{2}".format(self.collectoryUrl,
                                                        institutionCode,
                                                        collectionCode)
        print path
        result = self.collectoryGet(path).read()
        return json.loads(result)

    def addConsumerCollection(self, drUid, coUid):
        dataResource = self.search('dataResource', {'uid': drUid})
        linkedRecordConsumers = []
        linkedRecordConsumers.append(coUid)
        if 'linkedRecordConsumers' in dataResource:
            for consumer in dataResource['linkedRecordConsumers']:
                linkedRecordConsumers.append(consumer['uid'])
        drId = int(re.search('[0-9]+$', drUid).group(0)) + 1
        data = {}
        data['id'] = str(drId)
        data['consumers'] = ','.join(linkedRecordConsumers)
        data['_action_updateConsumers'] = 'Update'
        data_string = []
        for key, value in data.iteritems():
            data_string.append("{}={}".format(key, value))
        data_string = '&'.join(data_string)
        path = '{0}/dataResource/base'.format(self.collectoryUrl)
        header = {'Content-Type':'application/x-www-form-urlencoded'}
        response = self.collectoryPost(path, data_string, header)
        return response

    def collectoryGet (self, path):
        print path
        response = urllib2.urlopen(path)
        return response

    def collectoryPost (self,
                        path, 
                        data, 
                        headers={'Content-Type':'application/json'}):
        req  = urllib2.Request(path, data, headers)
        response = urllib2.urlopen(req)
        return response

    def search (self, entity, criteria):
        """Search an entity using the provided criteria has a dictionary

        """
        path = "{0}/ws/{1}/".format(self.collectoryUrl, entity)
        params = []
        for k, v in criteria.iteritems():
            params.append("{0}={1}".format(k, v))
        params = "&".join(params)
        path = "{0}?{1}".format(path, params)
        # print "Search in {0}".format(path)
        response = self.collectoryGet(path)
        return json.loads(response.read())

    def createProviderCode(self, code):
        path = "{0}/providerCode/save".format(self.collectoryUrl)
        header = {'Content-Type':'application/x-www-form-urlencoded'}
        data = "code={}&create=Create".format(code)
        return self.collectoryPost (path, data, header)
    
    def createProviderMap(self, collection_id, inst_coll_codes):
        inst_provider_list = [] 
        coll_provider_list = []
        for inst_code, coll_list in inst_coll_codes:
            inst_provider_code = ""
            if not inst_code:
                continue
            for coll_code in coll_list:
                if not coll_code:
                    continue
                lookup = self.lookup(inst_code, coll_code)
                if 'error' in lookup:
                    # providerCodes not found, create both and make the map
                    if not inst_provider_code:
                        result = self.createProviderCode (inst_code)
                        inst_provider_code = re.search('[0-9]+$',
                                    result.geturl()).group(0)
                        inst_provider_list.append(inst_provider_code)
                        print "last number is {}".format(inst_provider_code)
                    result = self.createProviderCode(coll_code)
                    coll_provider_code = re.search('[0-9]+$',
                              result.geturl()).group(0)
                    print "last number is {}".format(coll_provider_code)
                    coll_provider_list.append(coll_provider_code)

        # collectionId number in ProviderMap code add 1 to every collection code
        collection_id = str(int(collection_id) + 1)
        institution_codes = ['institutionCodes={0}'.format(i) for i in
                             inst_provider_list]
        institution_codes = '&'.join(institution_codes)
        collection_codes = ['collectionCodes={0}'.format(i) for i in
                            coll_provider_list]
        collection_codes = '&'.join(collection_codes)
        path = "{0}/providerMap/save".format(self.collectoryUrl)
        header = {'Content-Type':'application/x-www-form-urlencoded'}
        data = ("collection.id={0}&{1}&"
                "{2}&matchAnyCollectionCode=on&"
                "exact=on&create=Create").format(collection_id,
                                        institution_codes,
                                        collection_codes)
        result = self.collectoryPost (path, data, header)

    @classmethod
    def gbifOrganizationToAlaInstitution (cls, organization):
        """Take an organization object from Gbif API and convert it to Ala field
        names of Institutions
        """
        # print organization
        institution = {}
        institution['name'] = organization['title']
        institution['acronym'] = ''
        institution['guid'] = organization['key']
        institution['address'] = {}
        if 'city' in organization:
            institution['address']['city'] = organization['city']
        if 'country' in organization:
            institution['address']['country'] = organization['country']
        if 'phone' in organization:
            institution['phone'] = organization['phone']
        if 'email' in organization:
            institution['email'] = organization['email']
        if 'latitude' in organization:
            latitude = organization['latitude']
           # print latitude
           # latitude = str(latitude)
           # latitude = latitude.replace('.', ',')
            institution['latitude'] = latitude
           # print latitude
        if 'longitude' in organization:
            longitude = organization['longitude']
           # longitude = str(longitude)
           # longitude = longitude.replace('.', ',')
            institution['longitude'] = longitude
           # print longitude
        if 'homepage' in organization:
            institution['websiteUrl'] = organization['homepage']
        return institution


class MyTest(unittest.TestCase):
    def setUp(self):
        self.collectory = Collectory('http://172.16.16.85/collectory')

    def test_search(self):
        """test search functionality by any entity and criteria"""
        entity = 'institution'
        criteria = {'guid': '883ee5d0-9177-423d-a636-0284e8a4de46'}
        result = self.collectory.search(entity, criteria)
        self.assertIn('name', result[0])

    def test_provider(self):
        code = 'LD'
        result = self.collectory.createProviderCode(code)
        print result.geturl()
        print "last number is {}".format( re.search('[0-9]+$',
                                                    result.geturl()).group(0))
        self.assertEqual(200, result.getcode())

    def test_lookup(self):
        institutionCode = 'LD'
        collectionCode  = 'GENERAL'
        result = self.collectory.lookup(institutionCode, collectionCode)
        self.assertTrue(isinstance(result,dict))

    def test_addConsumerCollection(self):
        drUid = 'dr0'
        coUid = 'co334'
        result = self.collectory.addConsumerCollection(drUid, coUid)
        print result
        self.assertEqual(200, result.getcode())


if __name__ == '__main__':
    unittest.main()
