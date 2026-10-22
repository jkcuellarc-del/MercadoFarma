import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, joblib, itertools
import lab_experimento as L
from sklearn.linear_model import Ridge, ElasticNet, LinearRegression
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
P=L.PROC; ESP=L.ESP
d=pd.read_csv(P/'model_lab_scaled.csv',parse_dates=['Fecha']); raw=pd.read_csv(P/'model_lab.csv',parse_dates=['Fecha'])
sc=joblib.load(L.MODELS/'scaler_lab.joblib'); cols=sc['columns']; i=cols.index('y_mercado'); mu,sd=sc['scaler'].mean_[i],sc['scaler'].scale_[i]
d['yhat']=L.market_pred(d); d['ym_hat_s']=(d.yhat-mu)/sd
X0=['ipc_yoy','pib','pib_agro','smmlv','var_leche','var_res','var_cerdo','var_huevo','var_pollo']
def feats(df,fuente,cs):
    x=df[cs].copy()
    if 'y_mercado' in cs and fuente=='proj': x['y_mercado']=df.ym_hat_s
    return x
def model_factory(k,**kw):
    return {'ridge':lambda:Ridge(**kw),'enet':lambda:ElasticNet(max_iter=50000,**kw),'gbm':lambda:GradientBoostingRegressor(n_estimators=kw.get('n',100),learning_rate=.05,subsample=.8,max_depth=kw.get('md',2),min_samples_leaf=3,random_state=0),'rf':lambda:RandomForestRegressor(300,max_depth=kw.get('md',3),min_samples_leaf=3,random_state=0),'ols':lambda:LinearRegression()}[k]()
def pred(kind,a,b,mode,fuente='proj'):
    p=pd.Series(np.nan,index=b.index)
    if mode=='esp':
        for e in ESP:
            aa,bb=a[a.Especie==e],b[b.Especie==e]
            cs=kind[1]; m=model_factory(kind[0],**kind[2]).fit(aa[cs] if False else feats(aa,'obs',cs),aa.y_lab)
            p[bb.index]=m.predict(feats(bb,fuente,cs))
    else:  # pooled con dummies de especie
        cs=kind[1]+[f'esp_{e}' for e in ESP]
        m=model_factory(kind[0],**kind[2]).fit(feats(a,'obs',cs),a.y_lab); p[b.index]=m.predict(feats(b,fuente,cs))
    return p
cands={}
XM=['y_mercado']; XA=X0+['y_mercado']
for al in (0.1,1,10): cands[f'esp ridge a={al} solo y_mkt']=(('ridge',XM,dict(alpha=al)),'esp')
for al in (1,10,30): cands[f'esp ridge a={al} todo']=(('ridge',XA,dict(alpha=al)),'esp')
for al in (0.01,0.1,1): cands[f'pool ridge a={al} solo y_mkt']=(('ridge',XM,dict(alpha=al)),'pool')
for al in (1,10): cands[f'pool ridge a={al} todo']=(('ridge',XA,dict(alpha=al)),'pool')
for al in (.001,.01): cands[f'pool enet a={al}']=(('enet',XA,dict(alpha=al,l1_ratio=.5)),'pool')
for md in (1,2,3): cands[f'pool gbm md={md}']=(('gbm',XA,dict(md=md)),'pool')
cands['pool rf md=3']=(('rf',XA,dict(md=3)),'pool')
rows=[];PR={}
for nm,(k,mode) in cands.items():
    r={}
    for part,fs in (('val',['train']),('test',['train','validacion'])):
        a=d[d.split.isin(fs)]; b=d[d.split=={'val':'validacion','test':'prueba'}[part]]
        p=pred(k,a,b,mode); PR[(nm,part)]=p
        r['MAE_'+part]=np.abs(p-raw.loc[b.index,'y_lab']).mean()*100
        r['esc_'+part]=(L.esc(raw.loc[b.index,'y_lab'].to_numpy())==L.esc(p.to_numpy())).mean()
    rows.append(dict(modelo=nm,**r))
R=pd.DataFrame(rows).set_index('modelo'); R['MAE_medio']=(R.MAE_val+R.MAE_test)/2
pd.set_option('display.width',200,'display.float_format','{:,.2f}'.format)
print(R.sort_values('MAE_medio'))
R.sort_values('MAE_medio').to_csv(L.REP/'lab_candidatos.csv')
al_rows=[]
for al in (10,20,30,50,100,200,500,2000):
    r={'alpha':al}
    for part,fs in (('val',['train']),('test',['train','validacion'])):
        a=d[d.split.isin(fs)]; b=d[d.split=={'val':'validacion','test':'prueba'}[part]]
        p=pred(('ridge',XA,dict(alpha=al)),a,b,'esp'); y=raw.loc[b.index,'y_lab']
        r['MAE_'+part]=np.abs(p-y).mean()*100; r['sesgo_'+part]=(p-y).mean()*100
    r['MAE_medio']=(r['MAE_val']+r['MAE_test'])/2; al_rows.append(r)
A=pd.DataFrame(al_rows); A.to_csv(L.REP/'lab_alpha.csv',index=False); print(A)
