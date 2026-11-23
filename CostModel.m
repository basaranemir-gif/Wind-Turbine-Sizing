function coe=CostModel(Parameters,AEP_in)

%%the following cost model is based on work published in:
%% "Wind Turbine Design Cost and Scaling Model" by L. Fingersh, M. Hand, and A. Laxson. Technical Report NREL/TP-500-40566 (2006)


R=Parameters.RotorDiameter/2;

massblade=R^2.53*0.4948;  %LM- Glass fiber blade design
rating=Parameters.maxPower/1000; %%rated power in KW
sweptarea=pi*R^2;

etaAEP=0.9;  %efficiency in transforming aero-power in electro-power. Account for mechanical losses (main shaft bearing frictions, gear-box efficiency) and generator efficiency
    
hubheight=Parameters.HubHeight;
AEP=AEP_in/1000;
AEPnet=AEP*etaAEP; %AEP expresse in KWh
    
%w=0.1; n=20; FCR=(w*(1+w)^n)/((1+w)^n-1);
FCR=0.1185; %%fixed charge rate

%%Blade Material Cost Escalator (2002 to 2012)
BCE=171/148;
%%Labor Cost Escalator (2002 to 2012)
GDPE=13491.4/11528.1;

%BLADES COST
CostSingleBlade=((0.4019*R^3-955.24)*BCE + 2.7445*R^2.5025*GDPE)/(1-0.28);
CostBlades=CostSingleBlade*3;

%HUB COST
hubmass=0.954*(massblade)+5680.3;
CostHub=hubmass*4.25;

%Pitchsystem and pitch bearings COST
CostPitchSystem=2.28*(0.2106*(2*R)^2.6578);

%Spinner, Nose, Cone COST
nosemass=18.5*(2*R)-520.5;
CostNose=nosemass*5.57;

%Shaft COST
CostShaft=0.01*(2*R)^2.887;

%MainBearing COST
bearingmass=(2*R*8/600-0.033)*0.0092*(2*R)^2.5;
CostBearing=2*bearingmass*17.6;

%GearBox COST
CostGearBox=15.26*(rating)^1.249;

%Brakecoupling COST
CostBrake=1.9894*rating-0.1141;

%Generator COST
CostGenerator=rating*48.03;

%Electronics COST
CostElectronics=rating*79;

%YawDrive COST
CostYaw=2*(0.0339*(2*R)^2.964);

%Mainframe COST
CostMainFrame=17.92*(2*R)^1.672;

%ElectricalConnection COST
CostElectrical=rating*40;

%Hydraulic and Cooling COST
CostCooling=12*rating;

%Nacelle Cover COST
CostNacelle=11.537*rating+3849.7;

%Control, safety and monitoring COST
CostControl=35;

%Tower COST
massTower=0.2694*sweptarea*hubheight-1779;
CostTower=massTower*1.5*BCE;

%Foundation COST
CostFoundation=303.24*(hubheight*sweptarea)^0.4037;

%Transportation COST
CostTransportation=rating*(1.581/1e5*rating^2-0.0375*rating+54.7);

%Roads, Civil Work COST
CostRoads=rating*(2.17/1e6*rating^2-0.0145*rating+69.54);

%Assembly and Installation COST
CostInstallation=1.965*(hubheight*2*R)^1.1736;

%Electrical Interface COST
CostInterface=rating*(3.49/1e6*rating^2-0.0221*rating+109.7);

%Engineering COST
CostEng=rating*(9.94/1e4*rating+20.31);

%Levelized Replacement Cost COST
CostLRC=10.7*rating;

%O&M COST
CostOEM=0.007*AEP;

%LLC COST
CostLLC=0.00108*AEP;


%%Initial CAPITAL COST
ICC=CostEng+CostInterface+CostInstallation+CostRoads+CostTransportation+CostFoundation+...
    CostTower+CostControl+CostNacelle+CostCooling+CostElectrical+CostMainFrame+...
    CostYaw+CostElectronics+CostGenerator+ ...
    CostBrake+CostGearBox+CostBearing+CostShaft+CostNose+...
    CostPitchSystem+CostHub+CostBlades;
    

AOE=(CostLLC+CostOEM+CostLLC)./AEPnet;

%Installed Cost x KW
IC=ICC/rating;


%Capacity Factor
CF=ICC/AEPnet*100;

coe=(FCR*ICC)/AEPnet + AOE;

end