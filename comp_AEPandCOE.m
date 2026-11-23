function [AEP,coe] = comp_AEPandCOE(Parameters,PlotOption)

if nargin<2
    PlotOption=true; % default
end

% Plot symbols
Symb = {'-r','--b',':m','-.c'};  
WeibullStruct = Parameters.WeibullStruct;
WeibullStruct.k = 2;
WeibullStruct.integTime = 365*24;
WeibullStruct.MeanWindSpeed = Parameters.ContrCurves.Winds;

    
%% Compare AEP Vave 6.5m/s, 7.5m/s, 8.5m/s

% preallocate memory
AEP = NaN(size(WeibullStruct.Vave));
coe = AEP;

for k = 1:length(WeibullStruct.Vave)
    
    WeibullStruct.C = 2*WeibullStruct.Vave(k)/sqrt(pi);
    WeibullStruct.PDF = wblpdf(WeibullStruct.MeanWindSpeed,WeibullStruct.C,WeibullStruct.k);
    AEP(k) = WeibullStruct.integTime*trapz(WeibullStruct.MeanWindSpeed,WeibullStruct.PDF.*Parameters.ContrCurves.Power);
    coe(k) = CostModel(Parameters,AEP(k));

    if PlotOption
        if k==1
            figure
        end
        plot(WeibullStruct.MeanWindSpeed,WeibullStruct.PDF,Symb{k},'LineWidth',2);
        hold on; grid on; zoom on
    end
    
end

if PlotOption % add legend for all lines together
    ylabel('PDF [-]','FontSize',12,'FontWeight','bold');
    xlabel('Wind Speed [-]','FontSize',12,'FontWeight','bold');
    title('Weibull for WT classes','FontSize',12,'FontWeight','bold');
    legend(num2str(WeibullStruct.Vave'));
end

if PlotOption
    figure
    bar(AEP/1e6,'LineWidth',2,'LineStyle',':')
    colormap winter
    grid on; zoom on
    ylabel('AEP [MWh]','FontSize',12,'FontWeight','bold');
    xlabel('WT Class','FontSize',12,'FontWeight','bold');
    title('AEP','FontSize',12,'FontWeight','bold');
    
    figure
    bar(coe,'LineWidth',2,'LineStyle',':')
    colormap winter
    grid on; zoom on
    ylabel('CoE [$/KWh]','FontSize',12,'FontWeight','bold');
    xlabel('WT Class','FontSize',12,'FontWeight','bold');
    title('CoE','FontSize',12,'FontWeight','bold');
end

end
