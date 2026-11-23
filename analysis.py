"""
Wind Turbine Sizing — Python reproduction of the MATLAB exercise.
Replicates comp_ControlCurves.m and comp_AEPandCOE.m to produce the
numbers the assignment asks for (Tasks 2, 3, 6).
"""
import numpy as np
import scipy.io as sio
from scipy.interpolate import RectBivariateSpline
from scipy.optimize import minimize_scalar, brentq


def load_aero(fn):
    d = sio.loadmat(fn, struct_as_record=False, squeeze_me=True)
    a = d['AeroPerf']
    tsr = a.TSR[:, 0]        # axis-0 varies TSR
    pitch = a.Pitch[0, :]    # axis-1 varies Pitch
    Cp = a.Cp                # (nTSR, nPitch)
    Cq = a.Cq
    # spline interpolant of Cp(TSR, Pitch); replace NaN with 0 for the spline
    Cp_filled = np.nan_to_num(Cp, nan=0.0)
    cp_spline = RectBivariateSpline(tsr, pitch, Cp_filled, kx=3, ky=3)
    return tsr, pitch, Cp, Cq, cp_spline


def find_max_cp(tsr, pitch, cp_spline):
    """Find global Cp optimum over (TSR, Pitch) using the spline."""
    # coarse search then refine
    TT = np.linspace(tsr[0], tsr[-1], 400)
    PP = np.linspace(pitch[0], pitch[-1], 400)
    grid = cp_spline(TT, PP)
    i, j = np.unravel_index(np.argmax(grid), grid.shape)
    # refine with 2D scan around the peak
    t_lo, t_hi = max(tsr[0], TT[i] - 0.5), min(tsr[-1], TT[i] + 0.5)
    p_lo, p_hi = max(pitch[0], PP[j] - 1.0), min(pitch[-1], PP[j] + 1.0)
    TT2 = np.linspace(t_lo, t_hi, 400)
    PP2 = np.linspace(p_lo, p_hi, 400)
    g2 = cp_spline(TT2, PP2)
    i2, j2 = np.unravel_index(np.argmax(g2), g2.shape)
    tsr_opt, pitch_opt = TT2[i2], PP2[j2]
    cp_opt = float(cp_spline(tsr_opt, pitch_opt, grid=False))
    return tsr_opt, pitch_opt, cp_opt


def control_curves(params, cp_spline):
    rho = params['rho']
    R = params['D'] / 2
    maxVtip = params['maxVtip']
    maxPower = params['maxPower']
    tsr_opt = params['tsr_opt']
    pitch_opt = params['pitch_opt']
    cp_max = params['cp_max']

    winds = np.arange(params['Vin'], params['Vout'] + 1e-9, 0.1)
    V_tipmax_at_maxCp = maxVtip / tsr_opt   # wind speed where Vtip limit is hit in region 2

    n = len(winds)
    Cp = np.full(n, np.nan)
    TSR = np.full(n, np.nan)
    Pitch = np.full(n, np.nan)
    Omega = np.full(n, np.nan)
    Power = np.full(n, np.nan)

    # Region 2: constant max Cp
    i_end = n - 1
    is_212 = False
    for i in range(n):
        Cp[i] = cp_max
        TSR[i] = tsr_opt
        Pitch[i] = pitch_opt
        Omega[i] = TSR[i] * winds[i] / R
        Power[i] = 0.5 * rho * winds[i]**3 * R**2 * np.pi * cp_max
        if winds[i] > V_tipmax_at_maxCp:
            is_212 = True
            i_end = i
            break
        elif Power[i] > maxPower:
            is_212 = False
            i_end = i
            break

    # Region 2.5: Vtip limited, re-optimize pitch at fixed (lower) TSR
    if is_212:
        j_end = i_end
        for j in range(i_end, n):
            TSR[j] = maxVtip / winds[j]
            # maximize Cp over pitch at this TSR
            res = minimize_scalar(
                lambda p: -float(cp_spline(TSR[j], p, grid=False)),
                bounds=(pitch[0], pitch[-1]), method='bounded')
            Pitch[j] = res.x
            Cp[j] = -res.fun
            Omega[j] = TSR[j] * winds[j] / R
            Power[j] = 0.5 * rho * winds[j]**3 * R**2 * np.pi * Cp[j]
            j_end = j
            if Power[j] >= maxPower:
                Power[j] = maxPower
                break
    else:
        j_end = i_end - 1

    # Region 3: rated power, constant Omega
    for k in range(j_end + 1, n):
        Power[k] = maxPower
        Cp[k] = maxPower / (0.5 * rho * R**2 * np.pi * winds[k]**3)
        Omega[k] = Omega[k - 1]
        TSR[k] = Omega[k] * R / winds[k]

    return dict(winds=winds, Cp=Cp, TSR=TSR, Pitch=Pitch, Omega=Omega,
                Power=Power, is_212=is_212, idx=(i_end, j_end),
                V_tipmax_at_maxCp=V_tipmax_at_maxCp)


# ---- cost model (port of CostModel.m) ----
def cost_model(D, maxPower, hubheight, AEP_in):
    R = D / 2
    massblade = R**2.53 * 0.4948
    rating = maxPower / 1000.0      # kW
    sweptarea = np.pi * R**2
    etaAEP = 0.9
    AEP = AEP_in / 1000.0
    AEPnet = AEP * etaAEP
    FCR = 0.1185
    BCE = 171 / 148
    GDPE = 13491.4 / 11528.1

    CostSingleBlade = ((0.4019*R**3 - 955.24)*BCE + 2.7445*R**2.5025*GDPE)/(1-0.28)
    CostBlades = CostSingleBlade*3
    hubmass = 0.954*massblade + 5680.3
    CostHub = hubmass*4.25
    CostPitchSystem = 2.28*(0.2106*(2*R)**2.6578)
    nosemass = 18.5*(2*R) - 520.5
    CostNose = nosemass*5.57
    CostShaft = 0.01*(2*R)**2.887
    bearingmass = (2*R*8/600 - 0.033)*0.0092*(2*R)**2.5
    CostBearing = 2*bearingmass*17.6
    CostGearBox = 15.26*rating**1.249
    CostBrake = 1.9894*rating - 0.1141
    CostGenerator = rating*48.03
    CostElectronics = rating*79
    CostYaw = 2*(0.0339*(2*R)**2.964)
    CostMainFrame = 17.92*(2*R)**1.672
    CostElectrical = rating*40
    CostCooling = 12*rating
    CostNacelle = 11.537*rating + 3849.7
    CostControl = 35
    massTower = 0.2694*sweptarea*hubheight - 1779
    CostTower = massTower*1.5*BCE
    CostFoundation = 303.24*(hubheight*sweptarea)**0.4037
    CostTransportation = rating*(1.581/1e5*rating**2 - 0.0375*rating + 54.7)
    CostRoads = rating*(2.17/1e6*rating**2 - 0.0145*rating + 69.54)
    CostInstallation = 1.965*(hubheight*2*R)**1.1736
    CostInterface = rating*(3.49/1e6*rating**2 - 0.0221*rating + 109.7)
    CostEng = rating*(9.94/1e4*rating + 20.31)
    CostLRC = 10.7*rating
    CostOEM = 0.007*AEP
    CostLLC = 0.00108*AEP

    ICC = (CostEng+CostInterface+CostInstallation+CostRoads+CostTransportation+
           CostFoundation+CostTower+CostControl+CostNacelle+CostCooling+
           CostElectrical+CostMainFrame+CostYaw+CostElectronics+CostGenerator+
           CostBrake+CostGearBox+CostBearing+CostShaft+CostNose+CostPitchSystem+
           CostHub+CostBlades)
    AOE = (CostLLC + CostOEM + CostLLC)/AEPnet
    coe = (FCR*ICC)/AEPnet + AOE
    return coe, ICC, AEPnet


def aep_and_coe(cc, D, maxPower, hubheight, Vave_list):
    """Weibull-weighted AEP + CoE + capacity factor for each class."""
    k = 2.0
    integTime = 365*24
    V = cc['winds']
    P = cc['Power']
    out = []
    for Vave in Vave_list:
        C = 2*Vave/np.sqrt(np.pi)          # Rayleigh scale for k=2
        pdf = (k/C)*(V/C)**(k-1)*np.exp(-(V/C)**k)
        AEP = integTime*np.trapezoid(pdf*P, V)      # Wh (aero)
        coe, ICC, AEPnet = cost_model(D, maxPower, hubheight, AEP)
        # capacity factor = AEP_net / (rated_elec * hours)
        rated_elec = maxPower*0.9                    # electrical rated power [W]
        CF = (AEP*0.9) / (rated_elec * integTime)
        out.append(dict(Vave=Vave, AEP=AEP, coe=coe, ICC=ICC, CF=CF))
    return out


if __name__ == '__main__':
    # ---- 2 MW baseline ----
    global pitch
    tsr, pitch, Cp, Cq, cp_spline = load_aero('Cp-TSR-Pitch_table-2MW.mat')
    tsr_opt, pitch_opt, cp_max = find_max_cp(tsr, pitch, cp_spline)

    # Cq at region-2 operating point
    cq_spline = RectBivariateSpline(tsr, pitch, np.nan_to_num(Cq, nan=0.0), kx=3, ky=3)
    cq_r2 = float(cq_spline(tsr_opt, pitch_opt, grid=False))

    print('=== Task 2: Region 2 operating point (2 MW) ===')
    print(f'Cp (Region 2)    = {cp_max:.4f}')
    print(f'Cq (Region 2)    = {cq_r2:.5f}  (= Cp/TSR = {cp_max/tsr_opt:.5f})')
    print(f'lambda (Region 2)= {tsr_opt:.3f}')
    print(f'beta (Region 2)  = {pitch_opt:.3f} deg')

    D = 92.4
    R = D/2
    maxVtip = 72.0
    V_inf_tipmax = maxVtip / tsr_opt
    Omega_max = maxVtip / R           # rad/s
    print('\n=== Task 3: Vtip,max reached ===')
    print(f'V_inf(Vtip,max)  = {V_inf_tipmax:.3f} m/s')
    print(f'Omega_max        = {Omega_max:.4f} rad/s = {Omega_max*30/np.pi:.3f} rpm')

    params = dict(rho=1.225, D=D, maxVtip=maxVtip, maxPower=2e6/0.9,
                  tsr_opt=tsr_opt, pitch_opt=pitch_opt, cp_max=cp_max,
                  Vin=3, Vout=25)
    cc = control_curves(params, cp_spline)
    i_end, j_end = cc['idx']
    print('\n=== Task 4/5: regions ===')
    print(f'region 2.5 present : {cc["is_212"]}')
    print(f'Region 2 ends at V = {cc["winds"][i_end]:.1f} m/s (Vtip limit at {cc["V_tipmax_at_maxCp"]:.2f})')
    print(f'Region 2.5 ends / rated reached at V = {cc["winds"][j_end]:.1f} m/s')

    print('\n=== Task 6: AEP, CoE, Capacity Factor (2 MW) ===')
    res = aep_and_coe(cc, D, 2e6/0.9, 90, [10, 8.5, 7.5, 6])
    print(f'{"Class":<7}{"Vave":<7}{"AEP[MWh]":<12}{"CoE[$/kWh]":<12}{"CF[%]":<8}')
    for cls, r in zip(['I', 'II', 'III', 'IV'], res):
        print(f'{cls:<7}{r["Vave"]:<7}{r["AEP"]/1e6:<12.2f}{r["coe"]:<12.4f}{r["CF"]*100:<8.1f}')
