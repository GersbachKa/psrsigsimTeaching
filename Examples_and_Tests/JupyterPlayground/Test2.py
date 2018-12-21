import sys
sys.path.insert(0,'/home/kyle/GWA/NANOGrav/PsrSigSim/')
import psrsigsim as PSS
'''
Issues I'm facing:
1. I don't know how to update an existing figure. Has to do with origin or
   collumns or something... (Something I can fix)
2. The plot behaves completely differently depending on if it is shown in a
   browser or a jupyter notebook (something I've been messing with. Shouldn't
   be a big issues)
3. Bounds checking and switching how many pulses to show (I want 2 pulses for clarity)
4. Want to start the observation time somewhere in the middle, where pulses
   aren't screwy

'''

from bokeh.io import curdoc, output_file, show
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource
import bokeh.models.widgets as widgets
from bokeh.plotting import figure
import matplotlib.pyplot as plt

#output_file("PsrSigSim Bokeh Implementation.")

DM = widgets.TextInput(title='DM value', value='0.1')
button = widgets.Button(label='Generate Filter Bank',button_type='success')
# TODO: Add others change it up from textboxes


psr_dict = {}
psr_dict['f0'] = 1400                   #Central frequency
psr_dict['F0'] = 218                    #Pulsar spin freq
psr_dict['bw'] = 400                    #Bandwidth
psr_dict['Nf'] = 512                    #Frequency bins
psr_dict['ObsTime'] = 30                #Observation time
psr_dict['f_samp'] = 4                  #Sampling frequency
psr_dict['SignalType'] = "intensity"    #'intensity' which carries a Nf x Nt
#filterbank of pulses or 'voltage' which carries a 4 x Nt array of
#voltage vs. time pulses representing 4 stokes channels
psr_dict['dm'] = 0.1                     #Dispersion Measure Pescs/(CM^3)
# V_ISS -- Intersteller Scintilation Velocity
psr_dict['scint_bw'] =  15.6            #Scintilation Bandwidth
psr_dict['scint_timescale'] = 2630      #Scintilation Timescale
# pulsar -- pulsar name
# telescope -- telescope name(GBT or Arecibo)
psr_dict['freq_band'] = 1400            #Frequency band [327 ,430, 820, 1400, 2300]
# aperature -- aperature (m)
# area -- collecting area (m^2)
# Tsys -- system temp (K), total of receiver, sky, spillover, etc. (only needed for noise)
# name -- GBT or Arecibo
# tau_scatter -- scattering time (ms)
psr_dict['radiometer_noise'] =  False   #radiometer noise
psr_dict['data_type']='int8'            #
psr_dict['flux'] = 3
psr_dict['to_DM_Broaden'] = True
s1 =  PSS.Simulation(psr =  'J1713+0747' , sim_telescope= 'GBT',sim_ism= True, sim_scint= False, sim_dict = psr_dict,)
s1.simulate()
plotReturn = s1.signal.bokeh_filter_bank()


'''
Updating the filter bank
'''
def updateSim():
    s1 =  PSS.Simulation(psr =  'J1713+0747' , sim_telescope= 'GBT',sim_ism= True, sim_scint= False, sim_dict = psr_dict,)
    s1.simulate()
    plotReturn = s1.signal.bokeh_filter_bank()
    curdoc().add_root(row(inputs, plotReturn, width = 800))
    #print(type(plotReturn))

'''
ToggleButton
'''
def Button_click():
    print("Click")
    updateSim()
    pass

button.on_click(Button_click)

'''
DM updating here
'''
def update_DM(attrname, old, new):
    try:
        DMn = float(DM.value)
        psr_dict['dm'] = DMn
        print("DM updated to "+ str(DMn))
    except Exception as e:
        print("Some exception: "+e)
        #Do something to prevent it
        pass

DM.on_change('value',update_DM)


inputs = widgetbox(DM,button)

curdoc().add_root(row(inputs, plotReturn, width = 800))
curdoc().title = "DM variation"
