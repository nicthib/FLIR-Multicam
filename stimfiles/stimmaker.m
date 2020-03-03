function varargout = stimmaker(varargin)
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @stimmaker_OpeningFcn, ...
                   'gui_OutputFcn',  @stimmaker_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end


function stimmaker_OpeningFcn(hObject, ~, h, varargin)
h.output = hObject;
h.outputfreq = 1e4;
guidata(hObject, h);

function varargout = stimmaker_OutputFcn(hObject, ~, h) 
varargout{1} = h.output;

function loadstim_Callback(hObject, ~, h)
[FILENAME, PATHNAME, FILTERINDEX] = uigetfile('C:\Mohammed\stimfiles','Pick A stim file to load');
load(fullfile(PATHNAME,FILENAME),'DAQout','t');
h.DAQout = DAQout;
h.t = t;
plot(h.t,h.DAQout)
guidata(hObject,h)

function savestim_Callback(hObject, ~, h)
try
    DAQout = uint8(h.DAQout);
    stimtimes = h.stimtimes(1:2:end-1);
    cd C:\FLIR_Multi_Cam_HWTrig\stimfiles
    uisave({'DAQout','stimtimes'})
catch
    errordlg('No stim created. Make one first!')
    return
end

function randomstim_Callback(hObject, ~, h)
h.customstim.Value = str2num(h.customstim.String);
guidata(hObject,h)

function stimwidth_Callback(hObject, ~, h)
h.stimwidth.Value = str2num(h.stimwidth.String);
guidata(hObject,h)

function customstim_Callback(hObject, ~, h)
h.customstim.Value = str2num(h.customstim.String);
guidata(hObject,h)

function prestim_Callback(hObject, ~, h)
h.prestim.Value = str2double(h.prestim.String);
guidata(hObject,h)

function stim_Callback(hObject, ~, h)
h.stim.Value = str2double(h.stim.String);
guidata(hObject,h)

function poststim_Callback(hObject, ~, h)
h.poststim.Value = str2double(h.poststim.String);
guidata(hObject,h)

function makevanillastim_Callback(hObject, ~, h)
h.runlength = h.prestim.Value+h.stim.Value+h.poststim.Value;
h.stimmat = zeros([1,h.runlength*h.outputfreq]);
h.t = linspace(0,h.runlength,h.runlength*h.outputfreq);
h.stimmat(find(h.prestim.Value < h.t & h.t < h.prestim.Value + h.stim.Value)) = 1;
h.DAQout = createstim(h);
axes(h.axes1)
plot(h.t,h.DAQout)
h.info.stim = [h.prestim.Value h.stim.Value h.poststim.Value];
guidata(hObject,h)

function makecustomstim_Callback(hObject, ~, h)
h.runlength = sum(h.customstim.Value);
h.stimmat = zeros([1,h.runlength*h.outputfreq]);
h.t = linspace(0,h.runlength,h.runlength*h.outputfreq);
stim_t = cumsum(h.customstim.Value);
if mod(numel(stim_t),2) == 1
    for i = 2:2:numel(stim_t)
        h.stimmat(find(stim_t(i-1) < h.t & h.t<stim_t(i))) = 1;
    end
else
    errordlg('You put the custom stim numbers in wrong! Try again.')
    return
end
h.DAQout = createstim(h);
h.info.stim = str2num(h.customstim.String);
h.stimtimes = stim_t;
axes(h.axes1)
plot(h.t,h.DAQout)
guidata(hObject,h)

function makerandomstim_Callback(hObject, ~, h)
stim_t = makerandstim(h.randomstim.Value,h.stimwidth.Value);
h.runlength = sum(h.randomstim.Value);
h.stimmat = zeros([1,h.runlength*h.outputfreq]);
h.t = linspace(0,h.runlength,h.runlength*h.outputfreq);
stim_t = cumsum(stim_t);
for i = 2:2:numel(stim_t)
    h.stimmat(find(stim_t(i-1) < h.t & h.t<stim_t(i))) = 1;
end
h.DAQout = createstim(h);
h.info.stim = str2num(h.customstim.String);
h.stimtimes = stim_t;
axes(h.axes1)
plot(h.t,h.DAQout)
guidata(hObject,h)

function out = createstim(h)
freq = h.stimrep.Value;
duty = 50;
sq = 2.5+2.5*square(2*pi*freq.*h.t,duty);
out = sq.*h.stimmat;


function stimrep_Callback(hObject, ~, h)
h.stimrep.Value = str2double(h.stimrep.String);
guidata(hObject,h)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function stimrep_CreateFcn(hObject, ~, h)
function poststim_CreateFcn(hObject, ~, h)
function prestim_CreateFcn(hObject, ~, h)
function stim_CreateFcn(hObject, ~, h)
function customstim_CreateFcn(hObject, ~, h)
function randomstim_CreateFcn(hObject, ~, h)
function stimwidth_CreateFcn(hObject, ~, h)
