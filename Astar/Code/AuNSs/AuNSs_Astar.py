'''
    Processing formula data
'''
import pandas as pd
import os
import re
from enum import Enum


class FileFormat(Enum):
    txt = "txt"
    xlsx = "xlsx"


def get_file_data(fname):
    values = []
    tag_idx = -1
    with open(fname, encoding='gbk') as f:
        for idx, line in enumerate(f):
            v = line.split('\t')
            if v[0] == u'波长':
                tag_idx = idx
            if idx == tag_idx + 1:
                values = v
    usecols = list(filter(lambda x: x != '', [idx if val not in ['', '\n'] else '' for idx, val in enumerate(values)]))
    data = pd.read_csv(fname, encoding='gbk',
                       skiprows=list(range(0, tag_idx)) + list(range(tag_idx + 2 + 400, tag_idx + 400 + 100)), sep='\t',
                       usecols=usecols).iloc[:401, :]
    return data


'''
    Extract parameter files and UV-Vis files
'''
param_wave_dir_list = ["AuNSs_data/formula",
                       #                        "AuNSs_data/small size", "AuNSs_data/large size",
                       #                        "AuNSs_data/polyhedron",
                       "AuNSs_data/normalization"
                       ]
wave_name_dict = {}
param_name_list = []


def get_file_name_and_day(file_dir):
    for fname in os.listdir(file_dir):
        print(f'parse {fname}')
        if fname.startswith('.'):
            continue
        name, day, fmt = re.findall(f'([\u4e00-\u9fa5a-zA-Z]*)-([\w-]+).(txt|xlsx)', fname)[0]
        data = None
        file_path = f'{file_dir}/{fname}'
        #         print(file_path, fname, name, day, fmt)

        if FileFormat(fmt) == FileFormat.txt:
            data = get_file_data(file_path)
            wave_name_dict[f'{name}_{day}'] = data
        elif FileFormat(fmt) == FileFormat.xlsx:
            data = pd.read_excel(file_path)
            if 'normalization' in file_dir:
                wave_name_dict[f'{name}_{day}'] = data
            else:
                data['day'] = day
                param_name_list.append(data)
        else:
            print('error format')


for dir_name in param_wave_dir_list:
    get_file_name_and_day(dir_name)

data_param = pd.concat(param_name_list, axis=0).fillna(value=0).reset_index(drop=True)

'''
    Merge duplicate fields
'''
merge_cols = [['处理样品', '样品编号'], ['10mM HAuCl4', '10mM HAuCl4/mL']]
for col in merge_cols:
    data_param[col[0]] = data_param[col].apply(lambda x: max(x[col[0]], x[col[1]]), axis=1)
    del data_param[col[1]]

'''
    Match the target curve and calculate the error
'''

from math import ceil
import matplotlib.pyplot as plt

data_target = pd.read_excel('target/归一化uv数据.xlsx', skiprows=2)
use_cols = list(filter(lambda x: 'Unnamed' not in x, data_target.columns))
wave_cols = list(filter(lambda x: '波长' in x, use_cols))
absor_cols = list(filter(lambda x: '吸光度' in x, use_cols))
data_target = data_target[use_cols].fillna(value=0)

'''
    Round up the horizontal axis of the target curve
'''

for wcol, acol in zip(wave_cols, absor_cols):
    data_target[f'{wcol}_ceil'] = data_target[wcol].apply(lambda x: ceil(float(x)))
#     data_target.plot(x=wcol, y=acol, figsize=(20,10), title=data_target[[wcol]].columns[0])
#     plt.show()
# data_target.head()

data_target.plot(x=wcol, y=absor_cols, figsize=(20, 10), title='target_wave')
plt.show()

'''
    Extract wavelength and absorbance curves for each size
    Compare wavelengths in different intervals
'''
target_size = ['24nm', '54nm', '69nm', '88nm']
'''
    Calculate the difference in waveform curve
'''


def calculate_distance(source, source_index, source_val, target, target_index, target_val):
    try:
        data = pd.merge(left=source, right=target, left_on=source_index, right_on=target_index, how='inner')
        data['diff'] = data.apply(lambda row: pow((row[source_val] - row[target_val]), 2), axis=1)
        return data['diff'].mean()
    except Exception as e:
        print('exception:', e)
        print(source_index, source_val, target_index, target_val)
        print(source.dtypes)
        print(target.dtypes)


'''
    Calculate the difference in peak position
'''
from scipy.signal import find_peaks, peak_widths


# Absorbance wavelength
def get_peak_wave(arr, data):
    peaks, properties = find_peaks(arr, prominence=0.03)
    peak_wids = peak_widths(arr, peaks, rel_height=0.5)
    return data[peaks[0]]


# get_peak_wave(wave_name_dict['多面体AuNSs_20230921-2']['A1'].values,\
#                wave_name_dict['多面体AuNSs_20230921-2']['波长'].values)

def calculate_peak_diff(source_wave, source_idx, target_wave, target_idx):
    try:
        peak_source = get_peak_wave(source_wave, source_idx)
        peak_target = get_peak_wave(target_wave, target_idx)
        peak_error = peak_source - peak_target
        print(f'peak_source:{peak_source} peak_target:{peak_target} peak_error:{peak_error}')
        return peak_error, peak_source, peak_target

    except Exception as e:
        print('exception:', e)
        return 0, 0, 0


import numpy as np


def get_near_wave(wave_name_dict, wave_cols, absor_cols, data_target, exp_target_diff):
    for day, wave_data in wave_name_dict.items():
        #         wave_data['波长_int'] = wave_data['波长'].astype(int)
        for wave_index in wave_data.columns.values[1:]:
            diff_list = []
            wave_diff_list = []
            wave_pk_list = []
            for idx, (wcol, tcol) in enumerate(zip(wave_cols, absor_cols)):
                diff = calculate_distance(wave_data, '波长', wave_index, \
                                          data_target[[f'{wcol}_ceil', tcol]], f'{wcol}_ceil', tcol)
                diff_list.append(diff)
                print(wcol, tcol)
                wave_diff, soure_pk, target_pk = calculate_peak_diff(wave_data[wave_index].values,
                                                                     wave_data['波长'].values, \
                                                                     data_target[tcol].values, data_target[wcol].values)
                wave_diff_list.append(wave_diff)
                wave_pk_list.append([soure_pk, target_pk])

            # Take the curve with the smallest error
            min_idx = np.argmin(diff_list)
            min_idx_peak = np.argmin(wave_diff_list)
            min_idx_peak = 1

            print(day, wave_index, tcol, target_size[min_idx], diff_list[min_idx], \
                  target_size[min_idx_peak], wave_diff_list[min_idx_peak])
            exp_target_diff['day'].append(day)
            exp_target_diff['wave'].append(wave_index)
            exp_target_diff['size'].append(target_size[min_idx])
            exp_target_diff['wave_error'].append(diff_list[min_idx])
            exp_target_diff['peak_size'].append(target_size[min_idx_peak])
            exp_target_diff['peak_error'].append(wave_diff_list[min_idx_peak])
            exp_target_diff['peak_source'].append(wave_pk_list[min_idx_peak][0])
            exp_target_diff['peak_target'].append(wave_pk_list[min_idx_peak][1])


exp_target_diff = {
    'day': [],
    'wave': [],
    'size': [],
    'wave_error': [],
    'peak_size': [],
    'peak_error': [],
    'peak_source': [],
    'peak_target': []
}
get_near_wave(wave_name_dict, wave_cols, absor_cols, data_target, exp_target_diff)
exp_target_diff_pd = pd.DataFrame(exp_target_diff)
exp_target_diff_pd.to_excel('output/exp_target_diff.xlsx', header=True, index=False)

'''
    Merge parameters and curves
'''


def get_full_day_name(row):
    type_name = ''
    if row['type(1小尺寸，2-多面体，3-大尺寸)'] == 1.0:
        type_name = '小尺寸'
    elif row['type(1小尺寸，2-多面体，3-大尺寸)'] == 2.0:
        type_name = '多面体'
    elif row['type(1小尺寸，2-多面体，3-大尺寸)'] == 3.0:
        type_name = '大尺寸'
    day = row['day']
    idx = int(row['处理样品'])
    return f'{type_name}AuNSs_{day}-{idx}'


data_param['day'] = data_param.apply(get_full_day_name, axis=1)


def get_full_wave_name(name):
    mathes = re.findall(f'([\u4e00-\u9fa5a-zA-Z]*)_([\w]+)-([\w]+)', name)
    if len(mathes) > 0:
        return name
    else:
        return f'{name}-1'


exp_target_diff_pd['day'] = exp_target_diff_pd['day'].apply(get_full_wave_name)

exp_target_diff_pd['day_wave'] = exp_target_diff_pd.apply(lambda row: row['day'] + '_' + row['wave'], axis=1)
data_param['day_wave'] = data_param.apply(lambda row: row['day'] + '_' + row['波名'], axis=1)

data_param_wave = pd.merge(left=data_param, right=exp_target_diff_pd, on=['day_wave', 'day'], how='inner')
data_param_wave.head()

import random
import math


# Algorithm begins
# The close set is empty
# The open set is empty

# # Calculate valuation function


def get_zi_func(x, MAX_VALUE=1):
    # Normalization
    z = 1.0 - (x / MAX_VALUE)

    return z


def get_target_zi_func(x, TARGET_PEAK=7.0, MAX_VALUE=50):
    # Normalization closest to the goal
    z = 1 - (abs(x - TARGET_PEAK) / MAX_VALUE)

    return z


'''
    Minimum error in small-sized curves
'''


def small_size_filer(x):
    if re.findall(r'小尺寸AuNSs_', x['day']):
        return True
    else:
        return False


'''
    Minimum peak position error at polyhedral curves

'''


def polyhedron_filer(x):
    if re.findall(r'大尺寸AuNSs_2023(0627-1|0716-1|0716-2|0921-2|0921-3|0921-1|1226)', x['day']) and re.findall(r'A', x[
        'wave']):
        return True
    else:
        return False


data = data_param_wave[data_param_wave.apply(polyhedron_filer, axis=1)].reset_index(drop=True)


# Calculate hash
def get_hash_val(param_list):
    ret = []
    for param in param_list:
        param = str(round(param, 3))
        ret.append(param)
    return hash(tuple(ret))


# Build the initial closed set (including newly completed experiments), objectives, parameters, and zi list
target = 'peak_error'
params = ['0.1M AA', '10mM HAuCl4']
closed_set = {}


def build_closed_set(closed_set, data, params, target):
    for i in range(len(data)):
        zi = get_target_zi_func(data.loc[i, target])
        param_list = data.loc[i, params].values
        param_list_hash = get_hash_val(param_list)
        if param_list_hash not in closed_set:
            closed_set[param_list_hash] = (param_list, [zi])
        else:
            closed_set[param_list_hash][1].append(zi)


build_closed_set(closed_set, data, params, target)

# Construct the initial subset set as the open set based on the closed set, including parameters  si=zi_ist
open_set = {}

params_gap = [0.02, 0.02]  # Parameter variation amplitude
params_gap_thres = [0.04, 0.04]  # Parameter variation range
params_cnt_limit = 2

params_near_gap = [0.005, 0.01]
params_near_thres = [0.02, 0.02]


def build_open_set(open_set, closed_set):
    for pam_val_hash, (pam_val, zi) in closed_set.items():

        # For each one-dimensional parameter, find n nodes within the nearby threshold range
        for idx, param in enumerate(params):

            # Expansion in both positive and negative directions
            for i in range(2):
                cnt = 0
                gap = params_gap[idx]

                # Expanding to a specified quantity or to a specified boundary has an impact on everything within the range
                while cnt < params_cnt_limit and gap <= params_gap_thres[idx]:
                    new_pam_val = pam_val.copy()
                    new_pam_val[idx] += (gap if i == 0 else -gap)

                    if new_pam_val[idx] <= 0:
                        break

                    new_pam_val_hash = get_hash_val(new_pam_val)
                    if new_pam_val_hash not in closed_set and new_pam_val_hash not in open_set:
                        open_set[new_pam_val_hash] = [new_pam_val, []]
                        cnt += 1
                    gap += params_gap[idx]

            # Update in both positive and negative directions
            for i in range(2):
                gap = params_near_gap[idx]

                # Expand to the specified boundary and have an impact on everything within the range
                while gap <= params_near_thres[idx]:
                    new_pam_val = pam_val.copy()
                    new_pam_val[idx] += (gap if i == 0 else -gap)

                    new_pam_val_hash = get_hash_val(new_pam_val)
                    if new_pam_val_hash not in closed_set and new_pam_val_hash in open_set:
                        open_set[new_pam_val_hash][1].extend(zi.copy())
                    gap += params_near_gap[idx]


build_open_set(open_set, closed_set)

# Select the topk with the largest si from the open collection
open_set_params = list(open_set.values())
import math

param_exp_dict = {}
for param in params + ['si', 'near_num', 'near_zi']:
    param_exp_dict[param] = []
for pam_val, zi_list in open_set_params:
    #     print('before', pam_val)
    #     pam_val = [round(x, 3) for x in pam_val]
    #     print('after', pam_val)
    for idx, param in enumerate(params):
        #         print('after', pam_val[idx])
        param_exp_dict[param].append(pam_val[idx])
    param_exp_dict['si'].append(np.average(zi_list))
    param_exp_dict['near_num'].append(len(zi_list))
    param_exp_dict['near_zi'].append(zi_list)
param_exp_pd = pd.DataFrame(param_exp_dict)
param_exp_pd.sort_values(by='si', ascending=False, inplace=True)
param_exp_pd.to_excel('./output/param_exp_poly_all.xlsx', header=True, index=False)
param_exp_pd.head(50)