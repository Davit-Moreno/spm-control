import os 
import numpy as np 
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit as cf


def biexp(x,a,t1,t2): 
    return a*np.exp(-x/t1) + (1-a)*np.exp(-x/t2)

os.chdir(r"C:\Users\spmno\OneDrive\Documents\spm\Scan\Scan Data\2026-10-19\Scan14_X7.4Y40.8Z14.8_1e6_0.65uW_15min.ptu.g1.run")
#CHANGE THIS. Input run folder ########

data=np.genfromtxt("g1", delimiter=',')

os.chdir(r"C:\Users\spmno\OneDrive\Documents\spm\Intensity Traces\2024-09-03")
hh=np.genfromtxt(r'associated trPL 1 MHz 512ps.dat',delimiter='\t', skip_header=10)
hh0=hh[:,0]
hh1=hh[:,1]


ch0=data[:,3][:len(data)//2]
ch1=data[:,3][(len(data)//2):]
time_hh=(512/1000)*np.arange(0,len(hh),1)

ch0-=np.mean(ch0[-10:-1])
ch1-=np.mean(ch1[-10:-1])
ch0=ch0/np.max(ch0)
ch1=ch1/np.max(ch1)

time=data[:,1][:len(data)//2]

time-=time[np.argmax(ch0)]

p,c0 = cf(biexp, time[np.argmax(ch0):],ch0[np.argmax(ch0):],p0=[.5,25,5])
p1,c1 = cf(biexp, time[np.argmax(ch1):],ch1[np.argmax(ch1):],p0=[.5,25,5])



plt.figure(figsize=(8,8))
# plt.semilogy(time_hh,hh0)
# plt.semilogy(time/1000,ch0,'o', color='k',ms=3)
# plt.semilogy(time_hh,hh1)
# plt.figure()
plt.semilogy(time/1000,ch0,'o', color='b',label="Ch. 0")
plt.semilogy(time/1000,ch1,'o', color='r',label="Ch. 1")
plt.xlabel("Time (ns)", size=26)
plt.ylabel("Intensity (norm.)", size=26)
plt.tick_params(axis='both', labelsize=22)
plt.axis([-25,500,0.0001,1.1])
plt.tight_layout()
# plt.semilogy(time[np.argmax(ch1):],biexp(time[np.argmax(ch1):],*p1),'--',color='r',lw=5)
# plt.semilogy(time[np.argmax(ch0):],biexp(time[np.argmax(ch0):],*p),'--',color='g',lw=5)




plt.show()