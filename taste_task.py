# taste task. 5/1/2017
# red=practice; blue=prediction error
# run01 and run02 are practice (need to be paired with red) length 
# run03 and run04 are prediction error (need to be paired with blue) 
#water is pump 0
#milkshake is pump 1
#rinse is pump 2
#TR 2 sec
#the pkl file contains all study data as a back up including what files were used, useful for sanity checks
#the csv file is easier to read
#the log file also has onsets, but it has the time from when the .py file was initalized more accurate should be used for analysis
from psychopy import visual, core, data, gui, event, data, logging
import csv
import time
import serial
import numpy as N
import sys,os,pickle
import datetime
import exptutils
from exptutils import *

monSize = [800, 600]
info = {}
info['fullscr'] = False
info['port'] = '/dev/tty.USA19H1432P1.1'
info['participant'] = 'test'
info['run']=''
info['color']=''
info['session']=''

dlg = gui.DlgFromDict(info)
if not dlg.OK:
    core.quit()
#######################################
subdata={}

subdata['completed']=0
subdata['cwd']=os.getcwd()

clock=core.Clock()
datestamp=datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
subdata['datestamp']=datestamp
subdata['expt_title']='bromo_probabilistic'

subdata['response']={}
subdata['score']={}
subdata['rt']={}
subdata['stim_onset_time']={}
subdata['stim_log']={}
subdata['is_this_SS_trial']={}
subdata['SS']={}
subdata['broke_on_trial']={}
subdata['simulated_response']=False

subdata['onset']='/Users/gracer/Documents/bromo_task/onset_files/onsets_'+info['run']+info['session']
subdata['jitter']='/Users/gracer/Documents/bromo_task/onset_files/jitter_'+info['run']+info['session']
subdata['conds']='/Users/gracer/Documents/bromo_task/onset_files/conds_'+info['run']+info['session']
subdata['quit_key']='q'

#######################################
dataFileName='/Users/gracer/Documents/Output/%s_%s_subdata.log'%(info['participant'],info['session'],subdata['datestamp'])
logging.console.setLevel(logging.INFO)
logfile=logging.LogFile(dataFileName,level=logging.DATA)
ratings_and_onsets = []
#######################################
# Serial connection and commands setup
ser = serial.Serial(
                    port=info['port'],
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS
                   )
if not ser.isOpen():
    ser.open()

time.sleep(1)

#global settings
diameter=26.59
mls_H2O=3.0
mls_milk=3.0
delivery_time=6.0
cue_time=1.0
wait_time=1.0
rinse_time=2.0
mls_rinse=2.0
str='\r'
rate_H2O = mls_H2O*(3600.0/delivery_time)  # mls/hour 300
rate_milk = mls_milk*(3600.0/delivery_time)  # mls/hour 300
rate_rinse = mls_rinse*(3600.0/rinse_time)  # mls/hour 300


pump_setup = ['0VOL ML\r', '1VOL ML\r', '2VOL ML\r']
pump_phases=['0PHN01\r','1PHN01\r', '2PHN01\r','0CLDINF\r','1CLDINF\r','2CLDINF\r','0DIRINF\r','1DIRINF\r','2DIRINF\r','0RAT%iMH\r'%rate_H2O,'1RAT%iMH\r'%rate_milk,'2RAT%iMH\r'%rate_rinse,'0VOL%i%s'%(mls_H2O,str), '1VOL%i%s'%(mls_milk,str),'2VOL%i%s'%(mls_rinse,str),'0DIA%.2fMH\r'%diameter,'1DIA%.2fMH\r'%diameter, '2DIA%.2fMH\r'%diameter]

for c in pump_setup:
    ser.write(c)
    time.sleep(.25)

for c in pump_phases:
    ser.write(c)
    time.sleep(.25)

# HELPER FUNCTIONS
def show_instruction(instrStim):
    # shows an instruction until a key is hit.
    while True:
        instrStim.draw()
        win.flip()
        if len(event.getKeys()) > 0:
            break
        event.clearEvents()


def show_stim(stim, seconds):
    # shows a stim for a given number of seconds
    for frame in range(60 * seconds):
        stim.draw()
        win.flip()
        
def check_for_quit(subdata,win):
    k=event.getKeys()
    print 'checking for quit key %s'%subdata['quit_key']
    print 'found:',k
    if k.count(subdata['quit_key']) >0:# if subdata['quit_key'] is pressed...
        print 'quit key pressed'
        return True
    else:
        return False

# MONITOR
win = visual.Window(monSize, fullscr=info['fullscr'],
                    monitor='testMonitor', units='deg')
visual_stim=visual.ImageStim(win, image=N.zeros((300,300)), size=(0.75,0.75),units='height')
# STIMS
fixation_text = visual.TextStim(win, text='+', pos=(0, 0), height=2)

scan_trigger_text = visual.TextStim(win, text='Waiting for scan trigger...', pos=(0, 0))




#####################
#load in onset files#

onsets=[]
f=open(subdata['onset'],'r')
x = f.readlines()
for i in x:
    onsets.append(i.strip())

onsets=[float(i) for i in onsets]
print(onsets, 'onsets')

jitter=[]
g=open(subdata['jitter'],'r')
y = g.readlines()
for i in y:
    jitter.append(i.strip())
    
jitter=[float(i) for i in jitter]
print(jitter, 'jitter')

trialcond=N.loadtxt(subdata['conds'], dtype='int')
print(trialcond,'trial conditions')

ntrials=len(trialcond)
pump=N.zeros(ntrials)
#    pump zero is neutral, pump 1 is tasty, pump 2 is neutral
#    these need to match the onset files!
if info['color']=='red':
    pump[trialcond==1]=1 #tasty pump
    stim_images=['waterlogo.jpg','tasty.jpg']
else:
    stim_images=['waterlogo.jpg', 'tasty.jpg', 'tasty.jpg']
    pump[trialcond==0]=0 #water pump
    pump[trialcond==1]=1 #tasty pump
    pump[trialcond==2]=0 #water pump

subdata['trialdata']={}

            
"""
    The main run block!
"""

def run_block():

    # Await scan trigger
    while True:
        scan_trigger_text.draw()
        win.flip()
        if 'o' in event.waitKeys():
            logging.log(logging.DATA, "start key press")
            break
        event.clearEvents()

    clock=core.Clock()
    t = clock.getTime()
    ratings_and_onsets.append(['fixation',t])
    show_stim(fixation_text, 8)  # 8 sec blank screen with fixation cross
    t = clock.getTime()
    clock.reset()
    ratings_and_onsets.append(['start',t])
    #logging.log(logging.DATA, "start")
    for trial in range(ntrials):
        if check_for_quit(subdata,win):
            exptutils.shut_down_cleanly(subdata,win)
            sys.exit()
        
        trialdata={}
        trialdata['onset']=onsets[trial]
        visual_stim.setImage(stim_images[trialcond[trial]])#set which image appears
        print trial
        print 'condition %d'%trialcond[trial]
        print 'showing image: %s'%stim_images[trialcond[trial]]
        t = clock.getTime()
        ratings_and_onsets.append(["image=%s"%stim_images[trialcond[trial]],t])
        visual_stim.draw()#making image of the logo appear
        logging.log(logging.DATA, "image=%s"%stim_images[trialcond[trial]])
            
        while clock.getTime()<trialdata['onset']:
            pass
        win.flip()
            
        while clock.getTime()<(trialdata['onset']+cue_time):#show the image
            pass

        message=visual.TextStim(win, text='')#blank screen while the taste is delivered
        message.draw()
        win.flip()

        print 'injecting via pump at address %d'%pump[trial]
        logging.log(logging.DATA,"injecting via pump at address %d"%pump[trial])
        t = clock.getTime()
        ratings_and_onsets.append(["injecting via pump at address %d"%pump[trial], t])
        ser.write('%drun\r'%pump[trial])

        while clock.getTime()<(trialdata['onset']+cue_time+delivery_time):
            pass
        
        message=visual.TextStim(win, text='+', pos=(0, 0), height=2)#this lasts throught the wait
        message.draw()
        win.flip()
        t = clock.getTime()
        ratings_and_onsets.append(["wait", t])
        
        trialdata['dis']=[ser.write('0DIS\r'),ser.write('1DIS\r')]
        print(trialdata['dis'])

        while clock.getTime()<(trialdata['onset']+cue_time+delivery_time+wait_time):
            pass
        
        message=visual.TextStim(win, text='', pos=(0, 0), height=2)#this lasts throught the rinse 
        message.draw()
        win.flip()
                
        print 'injecting rinse via pump at address %d'%2
        t = clock.getTime()
        ratings_and_onsets.append(['injecting rinse via pump at address %d'%2, t])
        ser.write('%dRUN\r'%2)
        
        while clock.getTime()<(trialdata['onset']+cue_time+delivery_time+wait_time+rinse_time):
            pass

        message=visual.TextStim(win, text='+', pos=(0, 0), height=2)#lasts through the jitter 
        message.draw()
        win.flip()
        t = clock.getTime()
        ratings_and_onsets.append(["jitter", t])

        while clock.getTime()<(trialdata['onset']+cue_time+delivery_time+wait_time+rinse_time+jitter[trial]):
            pass
        
        t = clock.getTime()
        ratings_and_onsets.append(['end time', t])
        logging.log(logging.DATA,"finished")
        subdata['trialdata'][trial]=trialdata
    win.close()


run_block()

subdata.update(info)
f=open('/Users/gracer/Documents/Output/bromo_subdata_%s.pkl'%datestamp,'wb')
pickle.dump(subdata,f)
f.close()

myfile = open('/Users/gracer/Documents/Output/bromo_subdata_%s.csv'%datestamp.format(**info), 'wb')
wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
wr.writerow(['event','data'])
for row in ratings_and_onsets:
    wr.writerow(row)


core.quit()
