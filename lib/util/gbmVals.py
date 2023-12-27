
import datetime


class gbmVals:
    '''
    Class which contains gbm constant variables
    '''
    def __init__(self, ):
        ''' '''
        self.getTimes()
    def getTimes(self):
        #min Times
        then = datetime.datetime(2008, 6, 16)
        now = datetime.datetime.now()
        dif = now - then
        self.minMet = 235300000 #2008, 6, 16th, 09:07:44
        self.maxMet = self.minMet + dif.total_seconds()