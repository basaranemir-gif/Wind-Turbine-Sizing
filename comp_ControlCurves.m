function Parameters = comp_ControlCurves(Parameters,PlotOption)

if nargin<2
    PlotOption=true; % default
end

% assign inputs
rho = Parameters.airProp.rho;
LookUp = Parameters.AeroPerf;

%% Find Cp Max

% Generate initial guess by finding discrete maximum
[~,iMax] = max(LookUp.Cp,[],'all','omitnan','linear');
Pitch0 = LookUp.Pitch(iMax);
TSR0 = LookUp.TSR(iMax);

OptimizationOptions = optimset('LargeScale','off','Display','off','MaxIter',100,'TolFun',1.e-8,'TolCon',1.e-8,'MaxFunEvals',1000,'Algorithm','active-set');

% Refine guess by using smooth interpolation
p0 = [TSR0,Pitch0];
LB = [LookUp.TSR(1) LookUp.Pitch(1)];
UB = [LookUp.TSR(end) LookUp.Pitch(end)];

% interpolation of Cp-TSR-Pitch curves
CostFun = @(p)-interpn(LookUp.TSR,LookUp.Pitch,LookUp.Cp,p(1),p(2),'spline'); % 'cubic'
[p,maxCpNegative] =  fmincon(CostFun,p0,[],[],[],[],LB,UB,[],OptimizationOptions); % CpMaxParameters);
[TSR_maxCp,Pitch_maxCp] = deal(p(1),p(2));
maxCp = -maxCpNegative;

% save results
Parameters.ContrCurves.maxCp      = maxCp;
Parameters.ContrCurves.maxCpBeta  = Pitch_maxCp;
Parameters.ContrCurves.maxCpTSR   = TSR_maxCp;


%% Evaluate Performances

% w/o TipContraint
if Parameters.maxVtip == 0
    fprintf('\nWARNING !!! NO MAX Vtip CONSTRAINT!!!!!!!!!!!!!')
    Parameters.maxVtip = (Parameters.maxPower/(0.5*Parameters.airProp.rho*0.25*pi*Parameters.RotorDiameter^2*Parameters.ContrCurves.maxCp) )^(1/3)*Parameters.ContrCurves.maxCpTSR*1.001;
end

Parameters.ContrCurves.Winds = Parameters.minWindSpeed:.1:Parameters.maxWindSpeed;
Parameters.ContrCurves.maxWindSpeed_at_maxCp = Parameters.maxVtip/TSR_maxCp;


%% Region 2: max Cp

for i=1:length(Parameters.ContrCurves.Winds)
    
    Parameters.ContrCurves.Cp(i)    = maxCp;
    Parameters.ContrCurves.TSR(i)   = TSR_maxCp;
    Parameters.ContrCurves.Pitch(i) = Pitch_maxCp;
    Parameters.ContrCurves.Omega(i) = Parameters.ContrCurves.TSR(i)*Parameters.ContrCurves.Winds(i)/(Parameters.RotorDiameter/2);
    Parameters.ContrCurves.Power(i) = 0.5*rho*Parameters.ContrCurves.Winds(i)^3*(Parameters.RotorDiameter/2)^2*pi*Parameters.ContrCurves.maxCp;
    
    if Parameters.ContrCurves.Winds(i)>Parameters.ContrCurves.maxWindSpeed_at_maxCp
        Is_212 = true; % if true, there is a region 2 1/2
        break
    elseif  Parameters.ContrCurves.Power(i)>Parameters.maxPower
        Is_212 = false;
        break
    end
    
end


%% Region 2 1/2: max Vtip and high Cp

if Is_212==true
    
    for j=i:length(Parameters.ContrCurves.Winds)
        
        Parameters.ContrCurves.TSR(j)= Parameters.maxVtip/Parameters.ContrCurves.Winds(j);
        CostFun = @(p)-interpn(LookUp.TSR,LookUp.Pitch,LookUp.Cp,Parameters.ContrCurves.TSR(j),p,'spline'); % 'cubic'
        
        p0 = Pitch0;
        LB = LookUp.Pitch(1);        
        UB = LookUp.Pitch(end);
        [p,maxCpNegative] = fmincon(CostFun,p0,[],[],[],[],LB,UB,[],OptimizationOptions); % find pitch for maximum Cp at given TSR
        
        Parameters.ContrCurves.Pitch(j) = p;
        Parameters.ContrCurves.Cp(j)    = -maxCpNegative;
        Parameters.ContrCurves.Omega(j) = Parameters.ContrCurves.TSR(j)*Parameters.ContrCurves.Winds(j)/(Parameters.RotorDiameter/2);
        Parameters.ContrCurves.Power(j) = .5*rho*Parameters.ContrCurves.Winds(j)^3*(Parameters.RotorDiameter/2)^2*pi*Parameters.ContrCurves.maxCp;
        
        if Parameters.ContrCurves.Power(j)>=Parameters.maxPower
            Parameters.ContrCurves.Power(j)=Parameters.maxPower;
            break
        end
        
    end
    
else
    j=i-1;
end


%% Region 3: P_rated

for k=j+1:length(Parameters.ContrCurves.Winds)
    
    Parameters.ContrCurves.Power(k) = Parameters.maxPower;
    Parameters.ContrCurves.Cp(k)    = Parameters.maxPower/(.5*rho*(Parameters.RotorDiameter/2)^2*pi*(Parameters.ContrCurves.Winds(k))^3);
    Parameters.ContrCurves.Omega(k) = Parameters.ContrCurves.Omega(k-1);
    Parameters.ContrCurves.TSR(k)   = Parameters.ContrCurves.Omega(k)*Parameters.RotorDiameter/2/Parameters.ContrCurves.Winds(k);
    Parameters.ContrCurves.Pitch(k) = fsolve(@(x)(-interpn(LookUp.TSR,LookUp.Pitch,LookUp.Cp,Parameters.ContrCurves.TSR(k),x,'spline')+Parameters.ContrCurves.Cp(k)),20,optimoptions('fsolve','Display','off')); % find the pitch giving the desired Cp
    
end


%% Torque computation

Parameters.ContrCurves.Torque = Parameters.ContrCurves.Power./Parameters.ContrCurves.Omega;


%% Save wind speed indexes of transitions between regions

Parameters.ContrCurves.Indexes = [i j k];


%% FIGURES

if PlotOption
    
    % generate table with calculated curves
    figure;
    ContrCurves = table(Parameters.ContrCurves.Winds',Parameters.ContrCurves.Omega'*30/pi,Parameters.ContrCurves.Pitch',Parameters.ContrCurves.TSR',Parameters.ContrCurves.Torque'/1000,Parameters.ContrCurves.Power'/1000,...
        'VariableNames',{'V','Omega','Pitch','TSR','Torque','Power'});
    stackedplot(ContrCurves,'-r','XVariable','V','LineWidth',2,'GridVisible','on','Title','Turbine control','FontSize',12,'XLimits',[0 27],...
        'DisplayLabels',{'Rotor Speed [rpm]','Pitch [deg]','TSR [-]','Torque [kNm]','Power [kW]'},'XLabel','Wind speed [m/s]');
    
    figure('Name','Torque VS Omega', 'NumberTitle','off')
    plot(Parameters.ContrCurves.Omega*30/pi,Parameters.ContrCurves.Torque/1000,'-r');
    xlabel('\Omega [rpm]','FontSize',12,'FontWeight','bold');
    ylabel('Generator Torque [kNm]','FontSize',12,'FontWeight','bold');
    
    % figure,plot(Parameters.ContrCurves.Winds,Parameters.ContrCurves.Cpmax)
    
end

end
