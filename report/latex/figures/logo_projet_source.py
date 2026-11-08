import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Wedge
navy='#14206e'; blue='#1c548c'; light='#dfe7f2'
fig,ax=plt.subplots(figsize=(4,4)); ax.set_aspect('equal'); ax.axis('off')
ax.add_patch(Circle((0,0),1.0,fc='white',ec=navy,lw=6))      # nacelle
ax.add_patch(Circle((0,0),0.90,fc=light,ec=blue,lw=1.5))
# fan blades: curved swept blades
n=18
for k in range(n):
    a0=2*np.pi*k/n
    r=np.linspace(0.22,0.86,20)
    sweep=0.55*(r-0.22)
    th1=a0+sweep; th2=a0+sweep+0.17*(1-0.35*(r-0.22))
    xs=np.r_[r*np.cos(th1),(r*np.cos(th2))[::-1]]; ys=np.r_[r*np.sin(th1),(r*np.sin(th2))[::-1]]
    ax.add_patch(Polygon(np.c_[xs,ys],fc=navy,ec='white',lw=0.6))
ax.add_patch(Circle((0,0),0.24,fc=blue,ec='white',lw=2))       # spinner
ax.add_patch(Circle((0,0),0.08,fc='white',ec='none'))
ax.set_xlim(-1.08,1.08); ax.set_ylim(-1.08,1.08)
fig.savefig('emblem_turboreacteur.pdf',bbox_inches='tight',pad_inches=0.02,transparent=True)
fig.savefig('emblem_turboreacteur.png',dpi=300,bbox_inches='tight',pad_inches=0.02,transparent=True)
