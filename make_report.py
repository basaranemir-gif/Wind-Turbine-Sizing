"""
Wind Turbine Sizing — tüm görevlerin hesabı + grafikli PDF raporu (Türkçe).
MATLAB kodundaki (comp_ControlCurves.m, comp_AEPandCOE.m, CostModel.m) mantık
birebir Python'a portlandı. Çıktı: WindTurbineSizing_Rapor.pdf
"""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/mplcache')
os.makedirs('/tmp/mplcache', exist_ok=True)

import numpy as np
import scipy.io as sio
from scipy.interpolate import RectBivariateSpline
from scipy.optimize import minimize_scalar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.gridspec import GridSpec

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'figure.dpi': 110,
})

CLASSES = ['I', 'II', 'III', 'IV']
VAVE = [10, 8.5, 7.5, 6]
COLORS = ['#c0392b', '#2980b9', '#8e44ad', '#16a085']


# ---------------------------------------------------------------- data + model
def load_aero(fn):
    d = sio.loadmat(fn, struct_as_record=False, squeeze_me=True)
    a = d['AeroPerf']
    tsr = a.TSR[:, 0]
    pitch = a.Pitch[0, :]
    Cp = a.Cp
    Cq = a.Cq
    cp_spline = RectBivariateSpline(tsr, pitch, np.nan_to_num(Cp), kx=3, ky=3)
    cq_spline = RectBivariateSpline(tsr, pitch, np.nan_to_num(Cq), kx=3, ky=3)
    return dict(tsr=tsr, pitch=pitch, Cp=Cp, Cq=Cq,
                cp_spline=cp_spline, cq_spline=cq_spline, a=a)


def find_max_cp(aero):
    tsr, pitch, sp = aero['tsr'], aero['pitch'], aero['cp_spline']
    TT = np.linspace(tsr[0], tsr[-1], 500)
    PP = np.linspace(pitch[0], pitch[-1], 500)
    g = sp(TT, PP)
    i, j = np.unravel_index(np.argmax(g), g.shape)
    TT2 = np.linspace(max(tsr[0], TT[i]-0.4), min(tsr[-1], TT[i]+0.4), 500)
    PP2 = np.linspace(max(pitch[0], PP[j]-0.8), min(pitch[-1], PP[j]+0.8), 500)
    g2 = sp(TT2, PP2)
    i2, j2 = np.unravel_index(np.argmax(g2), g2.shape)
    t, p = TT2[i2], PP2[j2]
    return t, p, float(sp(t, p, grid=False))


def control_curves(prm, aero):
    rho, R = prm['rho'], prm['D']/2
    maxVtip, maxPower = prm['maxVtip'], prm['maxPower']
    tsr_opt, pitch_opt, cp_max = prm['tsr_opt'], prm['pitch_opt'], prm['cp_max']
    sp, pitch = aero['cp_spline'], aero['pitch']

    winds = np.arange(prm['Vin'], prm['Vout']+1e-9, 0.1)
    V_lim = maxVtip / tsr_opt
    n = len(winds)
    Cp = np.full(n, np.nan); TSR = Cp.copy(); Pit = Cp.copy()
    Om = Cp.copy(); Pow = Cp.copy()

    i_end, is212 = n-1, False
    for i in range(n):
        Cp[i], TSR[i], Pit[i] = cp_max, tsr_opt, pitch_opt
        Om[i] = TSR[i]*winds[i]/R
        Pow[i] = 0.5*rho*winds[i]**3*R**2*np.pi*cp_max
        if winds[i] > V_lim:
            is212, i_end = True, i; break
        elif Pow[i] > maxPower:
            is212, i_end = False, i; break

    if is212:
        j_end = i_end
        for j in range(i_end, n):
            TSR[j] = maxVtip/winds[j]
            r = minimize_scalar(lambda p: -float(sp(TSR[j], p, grid=False)),
                                bounds=(pitch[0], pitch[-1]), method='bounded')
            Pit[j], Cp[j] = r.x, -r.fun
            Om[j] = TSR[j]*winds[j]/R
            Pow[j] = 0.5*rho*winds[j]**3*R**2*np.pi*Cp[j]
            j_end = j
            if Pow[j] >= maxPower:
                Pow[j] = maxPower; break
    else:
        j_end = i_end-1

    for k in range(j_end+1, n):
        Pow[k] = maxPower
        Cp[k] = maxPower/(0.5*rho*R**2*np.pi*winds[k]**3)
        Om[k] = Om[k-1]
        TSR[k] = Om[k]*R/winds[k]

    return dict(winds=winds, Cp=Cp, TSR=TSR, Pitch=Pit, Omega=Om, Power=Pow,
                is212=is212, idx=(i_end, j_end), Vlim=V_lim)


def cost_model(D, maxPower, hub, AEP_in):
    R = D/2; rating = maxPower/1000.0; sweptarea = np.pi*R**2
    massblade = R**2.53*0.4948
    etaAEP = 0.9; AEP = AEP_in/1000.0; AEPnet = AEP*etaAEP
    FCR = 0.1185; BCE = 171/148; GDPE = 13491.4/11528.1
    CostBlades = 3*((0.4019*R**3-955.24)*BCE + 2.7445*R**2.5025*GDPE)/(1-0.28)
    CostHub = (0.954*massblade+5680.3)*4.25
    CostPitch = 2.28*(0.2106*(2*R)**2.6578)
    CostNose = (18.5*(2*R)-520.5)*5.57
    CostShaft = 0.01*(2*R)**2.887
    CostBearing = 2*((2*R*8/600-0.033)*0.0092*(2*R)**2.5)*17.6
    CostGear = 15.26*rating**1.249
    CostBrake = 1.9894*rating-0.1141
    CostGen = rating*48.03; CostElec = rating*79
    CostYaw = 2*(0.0339*(2*R)**2.964)
    CostMain = 17.92*(2*R)**1.672
    CostElectrical = rating*40; CostCool = 12*rating
    CostNac = 11.537*rating+3849.7; CostCtrl = 35
    CostTower = (0.2694*sweptarea*hub-1779)*1.5*BCE
    CostFound = 303.24*(hub*sweptarea)**0.4037
    CostTrans = rating*(1.581/1e5*rating**2-0.0375*rating+54.7)
    CostRoads = rating*(2.17/1e6*rating**2-0.0145*rating+69.54)
    CostInst = 1.965*(hub*2*R)**1.1736
    CostIface = rating*(3.49/1e6*rating**2-0.0221*rating+109.7)
    CostEng = rating*(9.94/1e4*rating+20.31)
    CostOEM = 0.007*AEP; CostLLC = 0.00108*AEP
    ICC = (CostEng+CostIface+CostInst+CostRoads+CostTrans+CostFound+CostTower+
           CostCtrl+CostNac+CostCool+CostElectrical+CostMain+CostYaw+CostElec+
           CostGen+CostBrake+CostGear+CostBearing+CostShaft+CostNose+CostPitch+
           CostHub+CostBlades)
    AOE = (CostLLC+CostOEM+CostLLC)/AEPnet
    coe = (FCR*ICC)/AEPnet + AOE
    return coe, ICC, AEPnet


def aep_coe(cc, D, maxPower, hub, vave_list):
    k = 2.0; T = 365*24
    V, P = cc['winds'], cc['Power']
    rows = []
    for Vave in vave_list:
        C = 2*Vave/np.sqrt(np.pi)
        pdf = (k/C)*(V/C)**(k-1)*np.exp(-(V/C)**k)
        AEP = T*np.trapezoid(pdf*P, V)
        coe, ICC, AEPnet = cost_model(D, maxPower, hub, AEP)
        CF = (AEP*0.9)/(maxPower*0.9*T)
        rows.append(dict(Vave=Vave, AEP=AEP, coe=coe, ICC=ICC, CF=CF, pdf=pdf))
    return rows


# ---------------------------------------------------------------- compute 2 MW
aero2 = load_aero('Cp-TSR-Pitch_table-2MW.mat')
tsr_opt, pitch_opt, cp_max = find_max_cp(aero2)
cq_r2 = float(aero2['cq_spline'](tsr_opt, pitch_opt, grid=False))

D0, maxVtip, hub0, maxP = 92.4, 72.0, 90.0, 2e6/0.9
R0 = D0/2
V_lim = maxVtip/tsr_opt
Omega_max = maxVtip/R0

prm0 = dict(rho=1.225, D=D0, maxVtip=maxVtip, maxPower=maxP,
            tsr_opt=tsr_opt, pitch_opt=pitch_opt, cp_max=cp_max, Vin=3, Vout=25)
cc0 = control_curves(prm0, aero2)
res0 = aep_coe(cc0, D0, maxP, hub0, VAVE)

# Task 7: rotor diameter sweep
Diam = np.arange(60, 115+1e-9, 2.5)
coe_D = np.zeros((len(Diam), 4))
for di, D in enumerate(Diam):
    p = dict(prm0); p['D'] = D
    cc = control_curves(p, aero2)
    for ci in range(4):
        C = 2*VAVE[ci]/np.sqrt(np.pi)
        V = cc['winds']
        pdf = (2/C)*(V/C)*np.exp(-(V/C)**2)
        AEP = 365*24*np.trapezoid(pdf*cc['Power'], V)
        coe_D[di, ci], _, _ = cost_model(D, maxP, hub0, AEP)
Dopt = Diam[np.argmin(coe_D, axis=0)]
coeDmin = np.min(coe_D, axis=0)

# Task 8: hub height sweep (log shear), diameter fixed at D0
Hub = np.arange(50, 160+1e-9, 5)
z0, zref = 0.2, 90.0
coe_H = np.zeros((len(Hub), 4))
for hi, H in enumerate(Hub):
    p = dict(prm0); p['D'] = D0
    cc = control_curves(p, aero2)
    shear = np.log(H/z0)/np.log(zref/z0)
    for ci in range(4):
        Vave_h = VAVE[ci]*shear
        C = 2*Vave_h/np.sqrt(np.pi)
        V = cc['winds']
        pdf = (2/C)*(V/C)*np.exp(-(V/C)**2)
        AEP = 365*24*np.trapezoid(pdf*cc['Power'], V)
        coe_H[hi, ci], _, _ = cost_model(D0, maxP, H, AEP)
Hopt = Hub[np.argmin(coe_H, axis=0)]
coeHmin = np.min(coe_H, axis=0)

# Task 9: combined D + H optimum (grid)
coe_DH = np.zeros((len(Diam), len(Hub), 4))
for di, D in enumerate(Diam):
    p = dict(prm0); p['D'] = D
    cc = control_curves(p, aero2)
    V = cc['winds']
    for hi, H in enumerate(Hub):
        shear = np.log(H/z0)/np.log(zref/z0)
        for ci in range(4):
            Vave_h = VAVE[ci]*shear
            C = 2*Vave_h/np.sqrt(np.pi)
            pdf = (2/C)*(V/C)*np.exp(-(V/C)**2)
            AEP = 365*24*np.trapezoid(pdf*cc['Power'], V)
            coe_DH[di, hi, ci], _, _ = cost_model(D, maxP, H, AEP)
combo = []
for ci in range(4):
    di, hi = np.unravel_index(np.argmin(coe_DH[:, :, ci]), coe_DH[:, :, ci].shape)
    combo.append((Diam[di], Hub[hi], coe_DH[di, hi, ci]))

# Task 10: 10 MW offshore
aero10 = load_aero('Cp-TSR-Pitch_table-10MW.mat')
t10, p10, cp10 = find_max_cp(aero10)
cq10 = float(aero10['cq_spline'](t10, p10, grid=False))
D10, Vtip10, hub10, maxP10 = 178.0, 90.0, 119.0, 10e6/0.9
prm10 = dict(rho=1.225, D=D10, maxVtip=Vtip10, maxPower=maxP10,
             tsr_opt=t10, pitch_opt=p10, cp_max=cp10, Vin=3, Vout=25)
cc10 = control_curves(prm10, aero10)
res10 = aep_coe(cc10, D10, maxP10, hub10, VAVE)
Diam10 = np.arange(140, 280+1e-9, 5)
coe_D10 = np.zeros((len(Diam10), 4))
for di, D in enumerate(Diam10):
    p = dict(prm10); p['D'] = D
    cc = control_curves(p, aero10)
    V = cc['winds']
    for ci in range(4):
        C = 2*VAVE[ci]/np.sqrt(np.pi)
        pdf = (2/C)*(V/C)*np.exp(-(V/C)**2)
        AEP = 365*24*np.trapezoid(pdf*cc['Power'], V)
        coe_D10[di, ci], _, _ = cost_model(D, maxP10, hub10, AEP)
Dopt10 = Diam10[np.argmin(coe_D10, axis=0)]

print('2MW R2: Cp=%.4f Cq=%.5f lam=%.3f beta=%.3f' % (cp_max, cq_r2, tsr_opt, pitch_opt))
print('Vlim=%.3f  Omega_max=%.3f rpm' % (V_lim, Omega_max*30/np.pi))
print('Dopt', Dopt, 'Hopt', Hopt)
print('combo', combo)
print('10MW R2: Cp=%.4f lam=%.3f beta=%.3f Dopt10=%s' % (cp10, t10, p10, Dopt10))

# save computed values for the PDF builder
np.savez('_results.npz',
         tsr_opt=tsr_opt, pitch_opt=pitch_opt, cp_max=cp_max, cq_r2=cq_r2,
         V_lim=V_lim, Omega_max=Omega_max, Diam=Diam, coe_D=coe_D, Dopt=Dopt,
         coeDmin=coeDmin, Hub=Hub, coe_H=coe_H, Hopt=Hopt, coeHmin=coeHmin,
         combo=np.array(combo), t10=t10, p10=p10, cp10=cp10, cq10=cq10,
         Diam10=Diam10, coe_D10=coe_D10, Dopt10=Dopt10)
print('computed OK')
