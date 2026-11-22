import sys, numpy as np, pandas as pd
from scipy.optimize import linprog
from scipy.sparse import lil_matrix
d=pd.read_csv(sys.argv[1],parse_dates=["datetime"])
P=d.pivot_table(index="date",columns="block",values="mcp_rs_mwh"); P.index=pd.to_datetime(P.index)
T=96; PMAX=2.5; EMIN,EMAX=2.0,20.0; ec=ed=np.sqrt(0.88)
def solve(p, deg, cyc):
    # vars: c(96), d(96), soc(96); grid MWh per block
    n=3*T; cost=np.r_[p, -(p-deg), np.zeros(T)]
    A=lil_matrix((T,n)); b=np.zeros(T)
    for t in range(T):
        A[t,2*T+t]=1; A[t,t]=-ec; A[t,T+t]=1/ed
        if t>0: A[t,2*T+t-1]=-1
        else: b[t]=EMIN
    Aub=lil_matrix((1,n)); Aub[0,T:2*T]=1/ed
    bnds=[(0,PMAX)]*(2*T)+[(EMIN,EMAX)]*(T-1)+[(EMIN,EMIN)]
    r=linprog(cost,A_ub=Aub.tocsr(),b_ub=[18*cyc],A_eq=A.tocsr(),b_eq=b,bounds=bnds,method="highs")
    x=r.x; return x[:T],x[T:2*T]
def settle(c,dd,p,deg): return float(p@dd - p@c - deg*dd.sum())
def fixed(p,deg):
    c=np.zeros(T); dd=np.zeros(T); c[44:60]=18/ec/16; dd[72:88]=18*ed/16; return settle(c,dd,p,deg)
test=P[P.index>="2025-11-22"]; rows=[]
for day,p in test.iterrows():
    p=p.values; prev=P.loc[day-pd.Timedelta(days=1)].values; wk=P.loc[day-pd.Timedelta(days=7)].values
    r={"date":day}
    for deg in (500,1000):
        for cyc in (1,2):
            c,dd=solve(p,deg,cyc); r[f"hind_{cyc}c_{deg}"]=settle(c,dd,p,deg)
        r[f"fixed_{deg}"]=fixed(p,deg)
        c,dd=solve(prev,deg,1); r[f"naive1d_{deg}"]=settle(c,dd,p,deg)
        c,dd=solve(prev,deg,2); r[f"naive1d_2c_{deg}"]=settle(c,dd,p,deg)
        c,dd=solve(wk,deg,1); r[f"naive7d_{deg}"]=settle(c,dd,p,deg)
    r["spread"]=p.max()-p.min(); rows.append(r)
R=pd.DataFrame(rows).set_index("date"); R.to_csv(sys.argv[2])
pd.set_option("display.width",200)
print("mean Rs/day (test 22 Nov 2025 - 21 Nov 2026):"); print(R.drop(columns="spread").mean().round(0).to_string())
for deg in (500,1000):
    h=R[f"hind_1c_{deg}"].sum()
    print(f"deg {deg}: capture fixed {R[f'fixed_{deg}'].sum()/h:.2f}, naive1d {R[f'naive1d_{deg}'].sum()/h:.2f}, naive7d {R[f'naive7d_{deg}'].sum()/h:.2f}; 2nd cycle adds {R[f'hind_2c_{deg}'].mean()-h/len(R):.0f}/day; fixed losing days {(R[f'fixed_{deg}']<0).mean():.2f}")
m=R.index.month; R["season"]=np.select([m.isin([3,4,5,6]),m.isin([7,8,9])],["Mar-Jun","Jul-Sep"],"Oct-Feb")
R["daytype"]=np.where(R.index.day_of_week>=5,"weekend","weekday"); R["spread_t"]=pd.qcut(R.spread,3,labels=["low","mid","high"])
cols=["hind_1c_500","fixed_500","naive1d_500"]
for g in ["season","daytype","spread_t"]:
    t=R.groupby(g,observed=True)[cols].mean().round(0); t["fixed_capture"]=(t.fixed_500/t.hind_1c_500).round(2); t["naive_capture"]=(t.naive1d_500/t.hind_1c_500).round(2); print(t.to_string())
