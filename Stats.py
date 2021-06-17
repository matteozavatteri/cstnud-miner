import math
from statistics import mean

MetricNames = ['MT', 'NC', 'NM', 'CR', 'TWC', 'TDC']

if __name__ == "__main__":
      for network in ["stn","stnd","stnu","cstn","stnud","cstnd","cstnu","cstnud"]:
            Metrics = dict()
            Metrics['MT']  = list()
            Metrics['NC']  = list()
            Metrics['NM']  = list()
            Metrics['TWC'] = list()
            Metrics['TDC'] = list()
            Metrics['CR']  = list()
            with open(f"mined/stats/{network}", "r") as f:
                  for line in f:
                        (log,S,MT,NC,NM,WC,TWC,DC,TDC) = tuple(line.strip().split())
                        S = int(S)
                        Metrics['MT'].append(float(MT))
                        NC = int(NC)
                        Metrics['NC'].append(NC)
                        NM = int(NM)
                        Metrics['NM'].append(NM)
                        WC = int(WC)
                        Metrics['TWC'].append(float(TWC))
                        DC = int(DC)
                        Metrics['TDC'].append(float(TDC))
                        assert(S  == 1)
                        assert(WC == 1)
                        assert(DC == 1)
                        Metrics['CR'].append(100 - ((NM * 100) / NC))
                        #print(f"{log}")
                  print(f"{network}")

                  for m in MetricNames:
                        print("{}=({},{},{})".format(m, round(min(Metrics[m]),3), round(mean(Metrics[m]),3),round(max(Metrics[m]),3)))
