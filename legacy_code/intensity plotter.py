import os 
import numpy as np 
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit as cf

def twogauss(x,a1,a2,m1,m2,s1,s2):
    return a1*np.exp(-(x-m1)**2/(2*s1**2))+ a2*np.exp(-(x-m2)**2/(2*s2**2))


os.chdir(r"C:\Users\spmno\OneDrive\Documents\spm\Scan\Scan Data\2026-10-12\Scan25_X11.6Y89Z9.6_CW_0.79uW_10min.ptu.g2.run") #input run folder
########

data=np.genfromtxt("intensity", delimiter=',')
data[:,0]=data[:,0]/10**6

bins, hist=np.histogram(data[:,3]+data[:,2],bins=50)
#p,c=cf(twogauss, hist[:-1], bins,p0=[65,120,60,120,20,20])

plt.figure(figsize=(8,8))
plt.plot(data[:,0], data[:,2], color='blue',label="Ch. 0")
plt.plot(data[:,0],data[:,3],color='red',label="Ch. 1")
#plt.plot(data[:,0],data[:,2]+data[:,3],color='black', alpha=0.5,label="Sum") #can comment out to get better view of single spads
plt.xlabel("Time (s)", size=26) 
plt.ylabel("Intensity (counts/100 ms)", size=26)
plt.tick_params(axis='both', labelsize=22)
leg=plt.legend(fontsize=22)
for l in leg.get_lines(): 
    l.set_linewidth(6)
plt.tight_layout()

'''
plt.figure(figsize=(8,8))
plt.hist(data[:,3]+data[:,2],bins=50, color='k', alpha=0.3)
plt.plot(hist, twogauss(hist, *p),'-',color='k', lw=3)
plt.xlabel("Occurrences", size=26)
plt.ylabel("Intensity (counts/100 ms)",size=26)
plt.tick_params(axis='both', labelsize=22)
plt.tight_layout()
plt.show()'''


plt.figure(figsize=(8,8))
plt.plot(data[:,0],data[:,2]+data[:,3],color='black', alpha=1)
plt.xlabel("Time (s)", size=26) 
plt.ylabel("Intensity (counts/100 ms)", size=26)
plt.tick_params(axis='both', labelsize=22)
plt.tight_layout()
plt.show()