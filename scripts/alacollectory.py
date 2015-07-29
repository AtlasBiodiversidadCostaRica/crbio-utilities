#!/usr/bin/env python
"""
simple tool to access service from Ala generic-collectory project https://github.com/AtlasOfLivingAustralia/generic-collectory
"""

import sys
import urllib2 
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

    def collectoryGet (self, path):
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
        if hasattr(organization, 'city'):
            institution['address']['city'] = organization['city']
        institution['address']['country'] = organization['country']
        if hasattr(organization,'phone'):
            institution['phone'] = organization['phone'][0]
        if hasattr(organization,'email'):
            institution['email'] = organization['email'][0]
        if hasattr(organization,'latitude'):
            institution['latitude'] = organization['latitude']
        if hasattr(organization,'longitude'):
            institution['longitude'] = organization['longitude']
        if hasattr(organization,'homepage'):
            institution['websiteUrl'] =organization['homepage'][0]
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
        self.assertEqual(200, result.getcode())

if __name__ == '__main__':
    unittest.main()
