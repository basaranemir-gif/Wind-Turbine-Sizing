close all
clearvars

addpath('.\Routines')
addpath('.\Input')

%% Evaluation

% load setup of the turbine
 Parameters = Setup;

% CALCULATE AND PLOT REGULATION TRAJECTORY
Handles = plot_AeroPerf(Parameters.AeroPerf);
Parameters = comp_ControlCurves(Parameters);
plot_ControlTrajectories(Parameters,Handles);

% COMPUTE AND PLOT AEP AND COE
[AEP,coe] = comp_AEPandCOE(Parameters);


%% rotor diameter optimization

% evaluate cost for a set of different rotor diameters
Diam = 70:5:105;
for k=1:length(Diam)
    Parameters.RotorDiameter = Diam(k);
    Parameters = comp_ControlCurves(Parameters,false);
    [~,coe(k,:)] = comp_AEPandCOE(Parameters,false);
end
[CoeMin,MinInd] = min(coe);

figure
axes(gcf,'XLim',[min(Diam) max(Diam)])
plot(Diam,coe)
hold on, box on, grid on
scatter(Diam(MinInd),CoeMin,'Marker','x','MarkerEdgeColor','red','LineWidth',1,'SizeData',50)
ylabel('CoE [$/kWh]','FontSize',12,'FontWeight','bold');
xlabel('Rotor Diameter [m]','FontSize',12,'FontWeight','bold');
legend('show',{'Class 1','Class 2','Class 3','Class 4','Minima'})


%% hub height optimization

% evaluate cost for a set of different hub heights
HubHeight = 50:10:160;
Parameters.HubHeightReference = 90;
Parameters.WeibullStruct.VaveOld = Parameters.WeibullStruct.Vave; % save original average wind speed
for k=1:length(HubHeight)
    Parameters.HubHeight = HubHeight(k);
    Parameters.WeibullStruct.Vave = Parameters.WeibullStruct.VaveOld.*(log(Parameters.HubHeight/0.2)/log(Parameters.HubHeightReference/0.2)); % caution, scale original wind speed!
    Parameters = comp_ControlCurves(Parameters,false);
    [~,coe(k,:)] = comp_AEPandCOE(Parameters,false);
end
[CoeMin,MinInd] = min(coe);

figure
plot(HubHeight,coe)
set(gca,'XLim',[min(HubHeight) max(HubHeight)])
hold on, box on, grid on
scatter(HubHeight(MinInd),CoeMin,'Marker','x','MarkerEdgeColor','red','LineWidth',1,'SizeData',50)
ylabel('CoE [$/KWh]','FontSize',12,'FontWeight','bold');
xlabel('Tower Height [m]','FontSize',12,'FontWeight','bold');
legend('show',{'Class 1','Class 2','Class 3','Class 4','Minima'});


