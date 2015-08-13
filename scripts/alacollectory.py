#!/usr/bin/env python
"""
simple tool to access service from Ala generic-collectory project https://github.com/AtlasOfLivingAustralia/generic-collectory
"""

import sys
import urllib2 
import urllib
import json
import unittest

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
        collectionCode  = collectionCode.replace('/','%252F')

        path = "{0}/ws/lookup/inst/{1}/coll/{2}".format(self.collectoryUrl,
                                                        institutionCode,
                                                        collectionCode)
        print path
        result = self.collectoryGet(path).read()
        return json.loads(result)

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
    
    def createProviderMap(self, collectionId, institutionCode, collectionCode):
        # collectionId number in ProviderMap code add 1 to every collection code
        collectionId = str(int(collectionId) + 1)
        path = "{0}/providerMap/save".format(self.collectoryUrl)
        header = {'Content-Type':'application/x-www-form-urlencoded'}
        data = ("collection.id={0}&institutionCodes={1}&"
                "collectionCodes={2}&matchAnyCollectionCode=on&"
                "exact=on&create=Create").format(collectionId,
                                        institutionCode,
                                        collectionCode)
        return self.collectoryPost (path, data, header)

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
            institution['phone'] = organization['phone'][0]
        if 'email' in organization:
            institution['email'] = organization['email'][0]
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
            institution['websiteUrl'] = organization['homepage'][0]
        return institution


class MyTest(unittest.TestCase):
    def setUp(self):
        self.collectory = Collectory('http://172.16.16.86/collectory')

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


if __name__ == '__main__':
    unittest.main()
