def findReviews(self, body):
        """
        Finds whether the words: 'Medical', 'Statistical' or 'Summary' are in body
        """
        for title in body: # scan through the review page for medical/statistical/summary review
            
            if u'Medical' in title:
                item["medReviewAvailable"] = True
                
            if u'Statistical' in title:
                item["statReviewAvailable"] = True
                
            if u'Summary' in title:
                sumReviewAvailable = True