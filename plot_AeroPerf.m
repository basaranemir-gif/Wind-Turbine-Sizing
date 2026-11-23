function Handles = plot_AeroPerf(LookUp)

% Cp(lambda,beta) curves in 2D
figure('Name','Cp VS TSR', 'NumberTitle','off');
hold on; zoom on; grid on;
plot(LookUp.TSR,LookUp.Cp,'LineWidth',1);
Handles(1) = gca;
xlabel('\lambda','FontSize',12,'FontWeight','bold');
ylabel('C_P','FontSize',12,'FontWeight','bold');
legend(num2str(unique(LookUp.Pitch)));
axis([-Inf Inf 0 0.6]);

% Cp curves in 3D
figure('Name','Cp surface', 'NumberTitle','off');
hold on; zoom on;
surf(LookUp.TSR,LookUp.Pitch,LookUp.Cp);
Handles(2) = gca;
xlabel('TSR [-]')
ylabel('Pitch [deg]')
zlabel('Cp [-]')

% Cq(lambda,beta) curves in 2D
figure('Name','Cq VS TSR', 'NumberTitle','off');
hold on; zoom on; grid on;
plot(LookUp.TSR,LookUp.Cq,'LineWidth',1);
Handles(3) = gca;
xlabel('\lambda','FontSize',12,'FontWeight','bold');
ylabel('C_Q','FontSize',12,'FontWeight','bold');
legend(num2str(unique(LookUp.Pitch)));
axis([-Inf Inf 0 0.1]);

end