import pyomo.environ as pyo
import pandas as pd
import numpy as np

def Run_Comu(Inputs): 
    
    Data = Inputs[0] # All prepared data to input in the OPT model
    t    = Inputs[1] 
    PL   = Inputs[2]
    PV   = Inputs[3]
    days = Inputs[4]
    
    PGi   = {}       # Power of each user for each day
    Pgii  = [0]*days # Power of each user for each day
    Pchid = [0]*days # Battery charge of each user for each day
    Pdiid = [0]*days # Battery discharge of each user for each day
    
    SOCi = {} # Battery SOC of each user for each day
    PC = {}
    
    CC_month = [0]*days
    PC_imp = [0]*days 
    PC_exp = [0]*days
    for m in list(range(days)):
        pPL_day ={} 
        pPV_day ={}
        ini = int(t * m)
        for T in Data['t']:
            for I in Data['i']:
                pPL_day[T,I] =  PL[ini:Data['t'][t-1]+ini,:][T-1,Data['i'].index(I)]
                pPV_day[T,I] =  PV[ini:Data['t'][t-1]+ini,:][T-1,Data['i'].index(I)]
        
        Data['pPl_day'] = pPL_day    
        Data['pPv_day'] = pPV_day   
        
        from Com import OptModel_C
        model_C = OptModel_C(Data) 
        opt = pyo.SolverFactory('gurobi')
        results = opt.solve(model_C, tee=False)
        
        ###### getting results:
        Pg         = pd.Series(data=[model_C.Pg[t,i]() for t,i in model_C.t*model_C.i], index=pd.MultiIndex.from_tuples(list(model_C.t*model_C.i)),name='Pg')

        SOC        = pd.Series(data=[model_C.SOC[t,i]() for t,i in model_C.t*model_C.i], index=pd.MultiIndex.from_tuples(list(model_C.t*model_C.i)),name='SOC_C') 
        Pc_imp     = pd.Series(data=[model_C.Pc_imp[t]() for t in model_C.t], index=list(model_C.t),name='Pc_imp') #Community power export (sell)
        Pc_exp     = pd.Series(data=[model_C.Pc_exp[t]() for t in model_C.t], index=list(model_C.t),name='Pc_exp') #Community power import (buy)

        Pbat_charg = pd.Series(data=[model_C.Pbat_charg[t,i]() for t,i in model_C.t*model_C.i], index=pd.MultiIndex.from_tuples(list(model_C.t*model_C.i)),name='Pbat_charg') #Pbat_pos
        Pbat_disch = pd.Series(data=[model_C.Pbat_disch[t,i]() for t,i in model_C.t*model_C.i], index=pd.MultiIndex.from_tuples(list(model_C.t*model_C.i)),name='Pbat_disch') #Pbat_neg

        pExpPrice  = pd.Series(data=[model_C.pExpPrice[t] for t in model_C.t], index=list(model_C.t),name='pExpPrice') #price parameter for buying electricity from the grid
        pImpPrice  = pd.Series(data=[model_C.pImpPrice[t] for t in model_C.t], index=list(model_C.t),name='pImpPrice') #price parameter for selling electricity to the grid
        
        PGi[m]   = Pg
        Pgii[m]  = Pg.unstack(level=1).values
        Pchid[m] = Pbat_charg.unstack(level=1).values
        Pdiid[m] = Pbat_disch.unstack(level=1).values
        
        PC[m]    = {'PcImport': Pc_imp, 'PcExport': Pc_exp}
        
        PC_imp[m]   = Pc_imp.values
        PC_exp[m]   = Pc_exp.values
        
        # costs per month
        CC_month[m]  = CC_day
        Data['pSOC_ini']  = {(1, key):values for key,values in SOC_init.items()}    # Update the initial SOC according to the previous sample SOC 
        Data['pSOC_last'] = {(Data['t'][-1]+1, key):values for key,values in SOC_init.items()}    
    
    
    #### To get Pg of each user
    Pcharg = pd.DataFrame(np.concatenate(Pchid, axis=0))
    Pdisch = pd.DataFrame(np.concatenate(Pdiid, axis=0))
    Pgi = pd.DataFrame(np.concatenate(Pgii, axis=0))
    Pcimp = pd.DataFrame(np.concatenate(PC_imp, axis=0))
    Pcexp = pd.DataFrame(np.concatenate(PC_exp, axis=0))
    
    return (Pcharg,Pdisch,Pgi,sum(CC_month),Pcimp,Pcexp)
