function Parameters = Setup

% Load data
Parameters = load('Cp-TSR-Pitch_table-2MW.mat');

Parameters.airProp.rho   = 1.225;    % Air density [kg/m^3]
Parameters.RotorDiameter = 92.4;     % Rotor Diameter [m]
Parameters.maxVtip       = 72;       % Max Tip Speed [m/s] : if 0 NO Constraint! 
Parameters.HubHeight     = 90;       % hub Height [m]
Parameters.maxPower      = 2e6*1/0.9;  % Shaft Power (i.e. aerodynamic power)[W]
Parameters.minWindSpeed  = 3;        % Cut-in  wind speed [m/s]
Parameters.maxWindSpeed  = 25;      % Cut-out wind speed [m/s]
Parameters.WeibullStruct.Vave = [10 8.5 7.5 6];  % Wind turbine class I, II, III and IV

end