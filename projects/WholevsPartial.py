import sys
sys.path.append('/home/dvmoors1/BB/ANALYSIS/DvM')

from IPython import embed
from eeg_analyses.EEG import * 

# subject specific info
sj_info = {'1': {'tracker': (False, '', ''),  'replace':{}}, # example replace: replace = {'15': {'session_1': {'B1': 'EXG7'}}}
			'2': {'tracker': (False, '', ''), 'replace':{}},
			'3': {'tracker': (False, '', ''), 'replace':{}},
			'4': {'tracker': (True, 'asc', 500), 'replace':{}},
			'5': {'tracker': (True, 'asc', 500), 'replace':{}},
			'6': {'tracker': (False, '', ''), 'replace':{}},
			'7': {'tracker': (False, '', ''), 'replace':{}},
			'8': {'tracker': (False, '', ''), 'replace':{}}} #  first trial is spoke trigger, because wrong experiment was started

# project specific info
montage = mne.channels.read_montage(kind='biosemi64')
eog =  ['V_up','V_do','H_r','H_l']
ref =  ['Ref_r','Ref_l']
trigger = [10,11,12,19]
t_min = -0.5
t_max = 0.75
flt_pad = 0.5
eeg_runs = [1]
binary = 3840
project_param = ['practice','nr_trials','trigger','condition',
				'block_type', 'cue','cue_loc','dev_0','dev_1','dev_2',
		         'test_order']

# set general plotting parameters
sns.set(font_scale=2.5)
sns.set_style('ticks', {'xtick.major.size': 10, 'ytick.major.size': 10})

class WholevsPartial(FolderStructure):

	def __init__(self): pass



if __name__ == '__main__':
	
	# Specify project parameters
	project_folder = '/home/dvmoors1/BB/Cue-whole/wholevspartial'
	os.chdir(project_folder)

	# run preprocessing
	preprocessing(sj = 4, session = 2, eog = eog, ref = ref, eeg_runs = eeg_runs, 
				  t_min = t_min, t_max = t_max, flt_pad = flt_pad, sj_info = sj_info, 
				  trigger = trigger, project_param = project_param, 
				  project_folder = project_folder, binary = binary, channel_plots = True, inspect = True)

	


