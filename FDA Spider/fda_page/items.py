# -*- coding: utf-8 -*-
from scrapy.item import Item, Field

class masterDrug_item(Item):
    Name = Field()
    link = Field()

class subDrug_item(Item):
    Name = Field()
    appType = Field() #ANDA/NDA/BLA etc.
    appNo = Field() #eg. '060518'
    marketStat = Field()
    approvDate = Field()
    Company = Field()
    reviewPageLink = Field()
    PPAReviewLink = Field()
    
    fileTabAvailable = Field()
    reviewAvailable = Field()
    medReviewAvailable = Field()
    statReviewAvailable = Field()
    sumReviewAvailable = Field()
    PatientPopulationAltered = Field()
    PPAReviewAvailable = Field()


    

