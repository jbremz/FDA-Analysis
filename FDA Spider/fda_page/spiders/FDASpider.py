from scrapy.spider import BaseSpider
from fda_page.items import masterDrug_item, subDrug_item
from scrapy import Selector, Request
from datetime import datetime

alpha = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','0-9']

start_urlList = []

for letter in alpha: #populate start urls list with each letter page
    start_urlList.append("http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.SearchResults_Browse&StepSize=100000&DrugInitial=" + letter)
    
test_urlList = ["http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.SearchResults_Browse&StepSize=100&DrugInitial=B"]
        
class FDASpider4(BaseSpider):
    name = "FDASpider"
    allowed_domains = ["www.accessdata.fda.gov"]
    start_urls = start_urlList
    drugListMaster = []
    subDrugList = []
    
    def start_requests(self):
        """
        Make request for each letter page
        
        """

        for url in self.start_urls:
            yield Request(url, callback=self.parseDrugList, dont_filter=True)



    def parseDrugList(self, response):
        """
        Scan through the current drug page (Master List) to find the link and name of each 'master drug' -> append to drugListMaster and yield request
        
        """
        hxs = Selector(response)
        links = hxs.xpath('//*[@id="user_provided"]/div[1]/table[2]//ul/li/a/@href').extract() #list of links
        names = hxs.xpath('//*[@id="user_provided"]/div[1]/table[2]//ul/li/a/text()').extract() #list of names
        
        for i in range(len(links)):
            item = masterDrug_item()
            item["Name"] = names[i]
            item["link"] = links[i]
            self.drugListMaster.append(item)
            url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/' + links[i]
            yield Request(url, callback=self.parseSubDrugList, meta={'url':url},dont_filter=True)
        
        
    def parseSubDrugList(self, response):
        """
        Scan through the current 'master drug' page to find links to each 'sub drug'
        
        """
        hxs = Selector(response)
        links = hxs.xpath('//b/a/@href').extract() #list of links - WARNING: is it a problem that I've already defined 'links' in parseDrugList?

        url = response.meta["url"]
        appNo = None
        name = hxs.xpath('//tr[1]/td[2]/strong/text()').extract() #drug name
        
        if len(links) != 0: #if page is a 'sub drug list' -> extract relevant info for each 'sub drug' on page (could use just 'if links:')
            for n in range(len(links)):
                item = subDrug_item()

                item["appNo"] = links[n].split('ApplNo=',1)[1][:6] #extracts application number from the href
                item["Name"] = name

                item["appType"] = '-'
                item["reviewPageLink"] = '-'
                item["PPAReviewLink"] = '-'
                item["fileTabAvailable"] = '-'
                item["reviewAvailable"] = '-'
                item["medReviewAvailable"] = '-'
                item["statReviewAvailable"] = '-'
                item["sumReviewAvailable"] = '-'
                item["PatientPopulationAltered"] = '-'
                item["PPAReviewAvailable"] = '-'
                item["Company"] = '-'
                item["approvDate"] = '-'

                mktStatNo = links[n].split('ProductMktStatus=',1)[1][:1] #extracts ProductMktStatus from href (1=Prescription,2=Over-the-counter,3=Discontinued,4=None (Tentative Approval))
                # item["link"] = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/' + links[n] # do we really need the link?

                if mktStatNo == '3': #product is discontinued -> yield product
                    item["marketStat"] = 'Discontinued'
                    yield item
                else:
                    appNo = item["appNo"]
                    url1 = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/' + links[n]
                    yield Request(url1, callback=self.parseSubDrugPage, meta={'url1':url1, 'cookiejar':appNo},dont_filter=True) #new cookiejar here labelled by application number
                    
        if len(links) == 0: #if page is already 'sub drug' page -> go straight to parseSubDrugPage 
            appNo = hxs.xpath('//tr[2]/td[2]/strong/text()').extract()[0].split()[1] # WARNING - sometimes gives 'out of range' error
            yield Request(url, callback=self.parseSubDrugPage, meta={'url':url, 'cookiejar':appNo}, dont_filter=True) #new cookiejar here labelled by application number
    
    def parseSubDrugPage(self, response):
        """
        Scan through the current 'sub drug page' to find: 
        - 'Approval History, Letters, Reviews, and Related Documents' link to follow
        - Assorted info about the sub drug
        
        """

        hxs = Selector(response)
        name = hxs.xpath('//tr[1]/td[2]/strong/text()').extract() #drug name
        appNo = response.meta['cookiejar']
        appID = hxs.xpath('//tr[2]/td[2]/strong/text()').extract() # eg. '(NDA) 021436'
        appType = appID[0].split()[0][1:-1] #eg. 'NDA' WARNING - also produces 'out of range' error
        company = hxs.xpath('//tr[4]/td[2]/strong/text()').extract()[0]
        approvDate = '-'
        try:
            approvDateTemp = hxs.xpath('//tr[5]/td[2]/strong/text()').extract()
            approvDateTemp = str(datetime.strptime(approvDateTemp[0], '%B %d, %Y').date())
            if len(approvDateTemp) == 10:
                approvDate = approvDateTemp
        except:
            print 'tagApp', approvDate
        fileTabLink = hxs.xpath('//tr[2]/td/ul/li/a/@href').extract()

        if fileTabLink: # is there a link to the doc page?
            fileTabURL = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/' + fileTabLink[0] #Finds link to file table
            fileTabAvailable = True
        else:
            fileTabAvailable = False

        mktStat = hxs.xpath('//tr[2]/td[5]/text()').extract() #marketing status of first (sub) sub drug in text not number form

        drugAppID = appID[0]
        drugMktStat = mktStat[0][:-1] #tidy this one up with the correct numbers
        
        if mktStat[0] == u'Discontinued\xa0' or appType == 'ANDA': #WARNING - make this accurate when len(mktStat) > 1
            item = subDrug_item()
            item["appNo"] = appNo
            item["appType"] = appType
            item["Name"] = name[0]
            item["marketStat"] = drugMktStat
            item["Company"] = company
            item["approvDate"] = approvDate
            item["reviewPageLink"] = '-'
            item["PPAReviewLink"] = '-'
            item["fileTabAvailable"] = '-'
            item["reviewAvailable"] = '-'
            item["medReviewAvailable"] = '-'
            item["statReviewAvailable"] = '-'
            item["sumReviewAvailable"] = '-'
            item["PatientPopulationAltered"] = '-'
            item["PPAReviewAvailable"] = '-'
            yield item
        
        else:
            yield Request(fileTabURL, callback=self.parseDocPage, meta={'cookiejar': appNo, 'name':name[0], 'drugAppID':drugAppID, 'appType':appType, 'drugMktStat':drugMktStat, 'fileTabAvailable':fileTabAvailable, 'Company':company, 'approvDate':approvDate}, dont_filter=True)
    
    
    def parseDocPage(self, response): #WARNING - add the patient population alteration part too
        """
        Scan through the page containg the table of relative documents and their links to find the link to the Review page and Summary Review

        """
        hxs = Selector(response)
        name = hxs.xpath('//tr[1]/td[2]/strong/text()').extract()[0]

        appNo = response.meta['cookiejar']
        drugAppID = response.meta['drugAppID']
        appType = response.meta['appType']
        drugMktStat = response.meta['drugMktStat']
        fileTabAvailable = response.meta['fileTabAvailable']
        company = response.meta['Company']
        approvDate = response.meta['approvDate']
        revAvailable = False
        sumReviewAvailable = False
        popRevAvailable = None

        # FOR THE 'INITIAL APPROVAL' CELL (at the bottom)

        suppNosRaw = hxs.xpath('//table[2]//tr[.]/td[2]/text()').extract() # the suppNos but with extra new lines that we just don't want
        suppNos = []
        for entry in suppNosRaw: # stripping the unwanted new lines from suppNosRaw and adding the right ones to suppNos 
            if u'\xa0' in entry:
                suppNos.append(entry)

        docIndex = str(len(suppNos) + 1)

        tagTexts = hxs.xpath('//table[2]//tr[' + docIndex + ']/td[4]/a[.]/text()').extract() #finds the text of the final cell in the table
        tagLinks = hxs.xpath('//table[2]//tr[' + docIndex + ']/td[4]/a[.]/@href').extract() #finds the links of the final cell in the table
        reviewLink = None

        if tagLinks: # for final cell
            if u'Review' in tagTexts[-1] and u'Summary' not in tagTexts[-1] and u'PDF' not in tagTexts[-1]: #check that the final link is actually for the review
                reviewLink = tagLinks[-1] # WARNING - only works if Review is indeed the last link in the cell (often is), otherwise need to use a for loop
            else:
                reviewLink = None
                revAvailable = False
        else:
            revAvailable = False

        if tagTexts: # for final cell
            # if u'Review' in tagTexts[-1] and u'PDF' in tagTexts[-1]: # WARNING - include this if we want to know whether the simple 'Review (PDF)' is available
            #     reviewAvailable = True
            if u'Summary' in tagTexts[-1]: # Finds if the Summary Review is available from the Doc table and sets the Review link accordingly
                sumReviewAvailable = True
                # sumLink = tagLinks[-1] # if sumLink is ever needed
                penulTagText = tagTexts[-2]
                if u'Review' in penulTagText:
                    reviewLink = tagLinks[-2]
        else:
            revAvailable = False # WARNING - don't need so many redefinitions of revAvailable in this function
        
        # FOR THE 'PATIENT POPULATION ALTERED' CELL

        patPopAltered = False # initial conditions
        popRevAvailable = False
        popReviewLink = None
        approvT = hxs.xpath('//table[2]//tr[.]/td[3]/text()').extract() # the "Approval Type" column

        popIndex = None
        popLinks = None
        for i in range(len(approvT)):
            if u'Population Altered' in approvT[i]:
                patPopAltered = True
                popIndex = str(i + 2)
                print 'tagpop', popIndex, appNo

        if popIndex:
            popTexts = hxs.xpath('//table[2]//tr[' + popIndex + ']/td[4]/a[.]/text()').extract() #finds the text of the population altered doc cell in the table
            popLinks = hxs.xpath('//table[2]//tr[' + popIndex + ']/td[4]/a[.]/@href').extract() #finds the links of the population altered doc cell in the table

        if popLinks and popIndex: # for patient population altered cell

            if u'Review' in popTexts[-1] and u'PDF' not in popTexts[-1]: #check that the final link is actually for the review
                popReviewLink = popLinks[-1] # WARNING - same as above, and also think about whether there's ever a Summary included here too
                popRevAvailable = True
            else:
                popReviewLink = None
                popRevAvailable = False
        else:
            popRevAvailable = False


        if not reviewLink: # WARNING - include more data here
            item = subDrug_item()
            item["PatientPopulationAltered"] = patPopAltered
            if popReviewLink == None:
                item["PPAReviewLink"] = '-'
            else:
                item["PPAReviewLink"] = popReviewLink
            item["PPAReviewAvailable"] = popRevAvailable
            item["appType"] = appType
            item["appNo"] = appNo
            item["Name"] = name
            item["marketStat"] = drugMktStat
            item["Company"] = company
            item["approvDate"] = approvDate
            item["reviewAvailable"] = False
            item["fileTabAvailable"] = '-'
            item["sumReviewAvailable"] = '-'
            item["reviewPageLink"] = '-'
            item["medReviewAvailable"] = '-'
            item["statReviewAvailable"] = '-'
            item["sumReviewAvailable"] = '-'
            print 'tagDoc'
            yield item
        
        else: 
            revAvailable = True
            yield Request(reviewLink, callback=self.parseReviewPage, meta={'cookiejar': appNo, 'name':name, 'sumReviewAvailable':sumReviewAvailable, 'drugAppID':drugAppID, 'appType':appType, 'drugMktStat':drugMktStat, 'revAvailable':revAvailable, 'fileTabAvailable':fileTabAvailable, 'patPopAltered':patPopAltered, 'popRevAvailable':popRevAvailable, 'popReviewLink':popReviewLink, 'Company':company, 'approvDate':approvDate}) # WARNING - does this need dont_filter, maybe not because it has unique url?
        
    def parseReviewPage(self, response):
        """
        Searches for Medical, Statistical and Summary Reviews in the Review page

        """

        hxs = Selector(response)

        name = response.meta['name']
        appNo = response.meta['cookiejar']
        drugAppID = response.meta['drugAppID']
        appType = response.meta['appType']
        drugMktStat = response.meta['drugMktStat']
        revAvailable = response.meta['revAvailable']
        fileTabAvailable = response.meta['fileTabAvailable']
        patPopAltered = response.meta['patPopAltered']
        popRevAvailable = response.meta['popRevAvailable']
        popReviewLink = response.meta['popReviewLink']
        company = response.meta['Company']
        approvDate = response.meta['approvDate']

        body1a = hxs.xpath('//ul/li[.]/p/text()').extract() #for the unlinked titles in 'a' formatting of page
        body2a = hxs.xpath('//ul/li[.]/p/a/text()').extract() #for the linked titles in 'a' formatting of page
        body1b = hxs.xpath('//ul/li[.]/text()').extract() #for the unlinked titles in 'b' formatting of page
        body2b = hxs.xpath('//ul/li[.]/a/text()').extract() #for the linked titles in 'b' formatting of page
        
        item = subDrug_item()

        item["medReviewAvailable"] = False
        item["statReviewAvailable"] = False
        item["sumReviewAvailable"] = response.meta['sumReviewAvailable']

        def findReviews(body):
            """
            Finds whether the words: 'Medical', 'Statistical' or 'Summary' are in body
            """

            for title in body: # scan through the review page for medical/statistical/summary review
                
                if u'Medical' in title:
                    item["medReviewAvailable"] = True
                    
                if u'Statistical' in title:
                    item["statReviewAvailable"] = True
                    
                if u'Summary' in title:
                    item["sumReviewAvailable"] = True


        findReviews(body1a)
        findReviews(body2a)
        findReviews(body1b)
        findReviews(body2b)

        item["fileTabAvailable"] = fileTabAvailable
        item["appType"] = appType
        item["appNo"] = appNo
        item["Name"] = name
        item["marketStat"] = drugMktStat
        item["reviewAvailable"] = True
        item["reviewPageLink"] = response.url
        item["PatientPopulationAltered"] = patPopAltered
        item["PPAReviewAvailable"] = popRevAvailable
        if popReviewLink == None:
            item["PPAReviewLink"] = '-'
        else:
            item["PPAReviewLink"] = popReviewLink
        item["Company"] = company
        item["approvDate"] = approvDate
        
        print 'tagm'
        yield item


                
#scrapy crawl FDASpider -o masterDrugList.csv -t csv
#http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.Overview&amp;DrugName=PENICILLIN%20V%20POTASSIUM
#//*[@id="user_provided"]/div[1]/table[2]/tbody/tr/td/table/tbody/tr[4]/td[2]/ul/li[.]/a
#'dont_redirect': True,'handle_httpstatus_list': [302],
#scrapy crawl FDASpider4 2>/dev/null | grep otherCount
#suppNos = hxs.xpath('//table[2]//tr[.]/td[2]/text()').extract()
# //table[2]/tbody/tr[.]/td[4]/a[.]



