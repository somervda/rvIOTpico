import time


class Statistic:
    total = 0
    samples = 0
    startTime = 0
    last = 0
    name=""


    def __init__(self,name): 
        self.name = name
        self.reset()

    def addSample(self,value):
        self.last=value
        self.total += value
        self.samples += 1
        # If first sample set start time
        if self.samples==1:
            self.startTime = time.time()
        print(self.name,value,self.total,self.samples,self.startTime,self.last)


    def reset(self):
        self.total = 0
        self.samples =0
        self.startTime = 0
        self.last = 0


    def get_average(self):
        if self.samples>0:
            return self.total / self.samples
        else:
            return 0

    def get_duration(self):
        return time.time() - self.startTime
    
    def get_samples(self):
        return self.samples

    def get_last(self):
        if self.samples>0:
            return self.last
        else:
            return None

    average = property(get_average) 
    duration = property(get_duration) 
    lastValue = property(get_last) 
    samples = property(get_samples)