function  plot_ControlTrajectories(Parameters,Handles)

TSR = Parameters.ContrCurves.TSR;
Cp = Parameters.ContrCurves.Cp;
Cq = Parameters.ContrCurves.Cp./TSR;
Pitch = Parameters.ContrCurves.Pitch;

% add trajectories to existing plots
TrajProp = {'Color','red','LineWidth',2,'Marker','+','MarkerIndices',1:5:length(TSR),'MarkerSize',8,'MarkerEdgeColor','black'};
plot(Handles(1),TSR,Cp,TrajProp{:})
plot3(Handles(2),TSR,Pitch,Cp,TrajProp{:})
plot(Handles(3),TSR,Cq,TrajProp{:})

end