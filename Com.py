import pyomo.environ as pyo

#%% model
def OptModel_C(data): 
    
    DT          = data['DT']
    t           = data['t']
    i           = data['i']
    pPl         = data['pPl_day']
    pPv         = data['pPv_day']
    Pgmax       = data['Pgmax']
    pSOC_ini    = data['pSOC_ini']
    pSOC_last   = data['pSOC_last']
    pEbat       = data['pEbat']
    pn          = data['pn']
    pBat_max    = data['pBat_max']
    pBat_min    = data['pBat_min']
    pExpPrice   = data['pExpPrice_day']
    pImpPrice   = data['pImpPrice_day']
    pSOC_min    = data['pSOC_min']
    pSOC_max    = data['pSOC_max']
    Comax       = data['Comax']
    model       = pyo.ConcreteModel(name = "Community Model")
    
    ############Sets

    model.t = pyo.Set(initialize = pyo.RangeSet(len(t)),ordered=True) 
    model.i = pyo.Set(initialize = i,ordered=True) # All users
    model.soct = pyo.Set(initialize = pyo.RangeSet(len(t)+1),ordered=True)  # T +1
    ############Parameters
    model.PV  = pyo.Param(model.t,model.i, initialize = pPv)
    model.Pl  = pyo.Param(model.t,model.i, initialize = pPl)

    model.SOC_ini   = pyo.Param(model.t,model.i,initialize=pSOC_ini)
    model.SOC_last  = pyo.Param(model.soct,model.i,initialize=pSOC_last)
    model.Ebat_max  = pyo.Param(model.i,initialize=pEbat)
    model.nbat      = pyo.Param(model.i,initialize=pn)  
    model.Pbat_max  = pyo.Param(model.i,initialize=pBat_max) 
    model.Pbat_min  = pyo.Param(model.i,initialize=pBat_min) 

    model.pExpPrice  = pyo.Param(model.t, initialize = pExpPrice)
    model.pImpPrice  = pyo.Param(model.t, initialize = pImpPrice)

    model.Pg_max   = pyo.Param(initialize = Pgmax)
    model.MCom      = pyo.Param(initialize = Comax)

    model.SOC_min = pyo.Param(model.i,initialize=pSOC_min)
    model.SOC_max = pyo.Param(model.i,initialize=pSOC_max)

    ############ Variables
    
    # model.Ub = pyo.Var(model.t,model.i, within=pyo.Binary)
    model.Uc = pyo.Var(model.t, within=pyo.Binary)
    
    model.Pc_imp = pyo.Var(model.t,domain = pyo.NonNegativeReals, bounds= (0.0, Pgmax)) 
    model.Pc_exp = pyo.Var(model.t,domain = pyo.NonNegativeReals, bounds= (0.0, Comax))  
    
    model.Pg = pyo.Var(model.t,model.i,domain = pyo.Reals, bounds= (-Pgmax*2, Pgmax)) 
    
    def Bbounds(model,t, i):
        return (pBat_min[i], pBat_max[i])
    model.Pbat_disch = pyo.Var(model.t,model.i, domain = pyo.NonNegativeReals, bounds= Bbounds)
    model.Pbat_charg = pyo.Var(model.t,model.i, domain = pyo.NonNegativeReals, bounds= Bbounds)
       
    def SOC_bound(model, soct, i):
        return (model.SOC_min[i], model.SOC_max[i])
    model.SOC = pyo.Var(model.soct,model.i,domain = pyo.NonNegativeReals, bounds = SOC_bound)
     
    ########### Constraints: 
    def PowerBalance(model, t, i):
        return model.PV[t,i] + model.Pbat_disch[t,i] + model.Pg[t,i] == model.Pl[t,i] + model.Pbat_charg[t,i] 
    model.balanceConstraint = pyo.Constraint(model.t,model.i, rule=PowerBalance, doc='Power Balance')
       
    #------------------    Community needs constraints
    def Com_pos(model,t):
        return model.Pc_imp[t] - model.Pc_exp[t] ==  sum(model.Pg[t,i] for i in model.i)
    model.CommunityConstraint = pyo.Constraint(model.t, rule=Com_pos, doc = 'Community needs')
    
    def MaxPCom_pos(model, t):
        return model.Pc_imp[t] <=  model.Uc[t]* model.Pg_max 
    model.MaxPCom_posConstraint = pyo.Constraint(model.t, rule=MaxPCom_pos, doc='Community purchase')

    def MaxPCom_neg(model, t):
        return model.Pc_exp[t] <= (1-model.Uc[t])*model.MCom 
    model.MaxPCom_negConstraint = pyo.Constraint(model.t, rule=MaxPCom_neg, doc='Community surplus')    
    #------------------   Energy storage ------------------ 
    
    def SOC_ini(model,i):
        return model.SOC[model.soct.first(),i] == model.SOC_ini[model.soct.first(),i]  
    model.SOC_Cons_inin= pyo.Constraint(model.i, rule = SOC_ini, doc='SoC init')  
    
    def SOC_last(model,i):
        return model.SOC[len(model.soct),i] >= model.SOC_last[len(model.soct),i] 
    model.SOC_Cons_last = pyo.Constraint(model.i, rule = SOC_last, doc='SoC last')  
    
    def SOC_update(model, t, i):
        return model.SOC[t+1,i] ==  model.SOC[t,i] + (model.nbat[i]*model.Pbat_charg[t,i] - (model.Pbat_disch[t,i]/(model.nbat[i])))*100*DT/(model.Ebat_max[i])
    model.SOC_Constraint = pyo.Constraint(model.t,model.i, rule = SOC_update, doc='SoC update')     
    
    ############  Objective Function   ###############################
    
    z =  sum(model.pImpPrice[t]*model.Pc_imp[t] - model.pExpPrice[t]*model.Pc_exp[t] for t in model.t)*DT  # [€/kWh]*[kW] = [€/h] 
  
    model.objective = pyo.Objective(rule = z)  
    return model
