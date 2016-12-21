import pandas as pd

#WARNING - may need to change between 'TRUE' <--> 'True' as excel changes the caps. 

df = pd.read_csv('masterDrugList2.csv')

iDs = df[(df.marketStat != 'Discontinued') & (df.appType != 'ANDA') & (df.appType != 'None (Tentative Approval)')] #interest drugs
iDs.date = pd.to_datetime(iDs.approvDate[iDs.approvDate != '-'])

#proportion of reviews available by year
iDs.propRevAv_yr = iDs[iDs.reviewAvailable == 'True'].reviewAvailable.groupby(iDs.date.dt.year).count()/iDs.reviewAvailable.groupby(iDs.date.dt.year).count()
iDs.propRevAv_yr = iDs.propRevAv_yr.fillna(0) #changes NaN values to 0

#proportion of medical reviews available by year
iDs.propMedRevAv_yr = iDs[iDs.medReviewAvailable == 'True'].medReviewAvailable.groupby(iDs.date.dt.year).count()/iDs.medReviewAvailable.groupby(iDs.date.dt.year).count()
iDs.propMedRevAv_yr = iDs.propMedRevAv_yr.fillna(0) #changes NaN values to 0

#proportion of statistical reviews available by year
iDs.propStatRevAv_yr = iDs[iDs.statReviewAvailable == 'True'].statReviewAvailable.groupby(iDs.date.dt.year).count()/iDs.statReviewAvailable.groupby(iDs.date.dt.year).count()
iDs.propStatRevAv_yr = iDs.propStatRevAv_yr.fillna(0) #changes NaN values to 0

#proportion of summary reviews available by year
iDs.propSumRevAv_yr = iDs[iDs.sumReviewAvailable == 'True'].sumReviewAvailable.groupby(iDs.date.dt.year).count()/iDs.sumReviewAvailable.groupby(iDs.date.dt.year).count()
iDs.propSumRevAv_yr = iDs.propSumRevAv_yr.fillna(0) #changes NaN values to 0

#proportion of PPA reviews available by year
iDs.propPPAAv_yr = iDs[(iDs.PatientPopulationAltered == 'True') & (iDs.PPAReviewAvailable == 'True')].PPAReviewAvailable.groupby(iDs.date.dt.year).count()/(iDs[iDs.PatientPopulationAltered == 'True'].PPAReviewAvailable.groupby(iDs.date.dt.year).count())
iDs.propPPAAv_yr = iDs.propPPAAv_yr.fillna(0) #changes NaN values to 0

#Total number of applications by year (of those which weren't discontinued etc.)
count = iDs.date.groupby(iDs.date.dt.year).count()

#table of companies by number of unavailable reviews
compUnavRev = iDs[iDs.reviewAvailable != 'True'].reviewAvailable.groupby(iDs.Company).count()
compUnavRev.name = 'No. of unavailable reviews'
compAvRev = iDs[iDs.reviewAvailable == 'True'].reviewAvailable.groupby(iDs.Company).count()
compAvRev.name = 'No. of available reviews'
companies = pd.concat([compUnavRev,compAvRev],axis=1).sort(columns='No. of unavailable reviews',ascending=False).fillna(0)

#marketing status info
marketStatInfo = df.groupby(df.marketStat).marketStat.count()

#proportion of reviews available

propRevAv = float(iDs[iDs.reviewAvailable == 'True'].reviewAvailable.count())/float(iDs.reviewAvailable.count())
propPPAAv = float(iDs[(iDs.PatientPopulationAltered == 'True') & (iDs.PPAReviewAvailable == 'True')].reviewAvailable.count())/float(iDs[iDs.PatientPopulationAltered == 'True'].PatientPopulationAltered.count())
propMedRevAv = float(iDs[iDs.medReviewAvailable == 'True'].medReviewAvailable.count())/float(iDs.medReviewAvailable.count())
propStatRevAv = float(iDs[iDs.statReviewAvailable == 'True'].statReviewAvailable.count())/float(iDs.statReviewAvailable.count())
propSumRevAv = float(iDs[iDs.sumReviewAvailable == 'True'].sumReviewAvailable.count())/float(iDs.sumReviewAvailable.count())

summaryTable = pd.DataFrame([pd.Series(['Main Reviews','PPA Reviews','Medical Reviews','Statistical Reviews','Summary Reviews']),pd.Series([propRevAv,propPPAAv,propMedRevAv,propStatRevAv,propSumRevAv])]).T
summaryTable.columns = ['Review Type','Proportion Available']

#proportion of reviews available by year
#iDs.propRevAv_yr.plot(kind="bar")

#proportion of PPA reviews available by year
#iDs.propPPAAv_yr.plot(kind="bar")
