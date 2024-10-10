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
param_wave_dir_list = ["AgNCs_data/formula",

                       "AgNCs_data/normalization"
                       ]
wave_name_dict = {}
param_name_list = []


def get_file_name_and_day(file_dir):
    for fname in os.listdir(file_dir):
        print(f'parse {fname}')
        if fname.startswith('.'):
            continue
        name, day, fmt = re.findall(f'([\u4e00-\u9fa5a-zA-Z]*)-([\w-]+).(txt|xlsx)', fname)[0]  # 删除ipynb_check
        data = None
        file_path = f'{file_dir}/{fname}'
        #         print(file_path, fname, name, day, fmt)

        if FileFormat(fmt) == FileFormat.txt:
            data = get_file_data(file_path)
            wave_name_dict[f'{name}_{day}'] = data
        elif FileFormat(fmt) == FileFormat.xlsx:
            data = pd.read_excel(file_path)
            if '归一化' in file_dir:
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
     Match the target curve and calculate the error
'''

from math import ceil
import matplotlib.pyplot as plt

data_target = pd.read_excel('target/AgNCs归一化uv数据.xlsx', skiprows=2)
use_cols = list(filter(lambda x: 'Unnamed' not in x, data_target.columns))
wave_cols = list(filter(lambda x: '波长' in x, use_cols))
absor_cols = list(filter(lambda x: '吸光度' in x, use_cols))
data_target = data_target[use_cols].fillna(value=0)

'''
    Round up the horizontal axis of the target curve
'''

for wcol, acol in zip(wave_cols, absor_cols):
    data_target[wcol] = data_target[wcol].apply(lambda x: ceil(float(x)))
#     data_target.plot(x=wcol, y=acol, figsize=(20,10), title=data_target[[wcol]].columns[0])
#     plt.show()
# data_target.head()

data_target.plot(x=wcol, y=absor_cols, figsize=(20, 10), title='target_wave')
plt.show()

'''
    Extract wavelength and absorbance curves for each size
    Compare wavelengths in different intervals
'''
target_size = ['23nm', '35nm', '43nm', '60nm']


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


# calculate_distance(wave_name_dict['20230716'], '波长', 'A1', data_target[[wave_cols[0], absor_cols[0]]], wave_cols[0], absor_cols[0])

import numpy as np


def get_near_wave(wave_name_dict, wave_cols, absor_cols, data_target, exp_target_diff):
    for day, wave_data in wave_name_dict.items():
        wave_data['波长'] = wave_data['波长'].astype(int)
        #         wave_data[wave_data.columns[1:]] = wave_data[wave_data.columns[1:]].astype(float)

        for source_index in wave_data.columns.values[1:]:
            diff_list = []
            for idx, (wcol, tcol) in enumerate(zip(wave_cols, absor_cols)):
                diff = calculate_distance(wave_data, '波长', source_index, \
                                          data_target[[wcol, tcol]], wcol, tcol)

                diff_list.append(diff)
            min_idx = np.argmin(diff_list)

            min_idx = 3

            print(day, source_index, tcol, target_size[min_idx], diff_list[min_idx])
            exp_target_diff['day'].append(day)
            exp_target_diff['wave'].append(source_index)
            exp_target_diff['size'].append(target_size[min_idx])
            exp_target_diff['wave_error'].append(diff_list[min_idx])


exp_target_diff = {
    'day': [],
    'wave': [],
    'size': [],
    'wave_error': []
}
get_near_wave(wave_name_dict, wave_cols, absor_cols, data_target, exp_target_diff)
exp_target_diff_pd = pd.DataFrame(exp_target_diff)
exp_target_diff_pd.to_excel('output/exp_target_AgNC_diff.xlsx', header=True, index=False)

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
    idx = int(row['样品编号'])
    return f'{type_name}AgNCs_{day}-{idx}'


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


# Calculate valuation function

def get_zi_func(x, MAX_VALUE=1):
    # Normalization
    z = 1.0 - (x / MAX_VALUE)

    return z


'''
    Minimum error in small-sized curves
'''


def small_size_filer(x):
    if re.findall(r'AgNCs_', x['day']):
        return True
    else:
        return False


data = data_param_wave[data_param_wave.apply(small_size_filer, axis=1)].reset_index(drop=True)

# Build the initial closed set (including newly completed experiments), objectives, parameters, and zi list
target = 'wave_error'
params = ['H2O/mL', '0.1M CF3COOAg/mL', 'Seed/mL']
closed_set = {}


def build_closed_set(closed_set, data, params, target):
    for i in range(len(data)):
        zi = get_zi_func(data.loc[i, target])
        param_list = data.loc[i, params].values
        param_list_hash = hash(tuple(param_list))
        if param_list_hash not in closed_set:
            closed_set[param_list_hash] = (param_list, [zi])
        else:
            closed_set[param_list_hash][1].append(zi)


build_closed_set(closed_set, data, params, target)

# Construct the initial subset set as the open set based on the closed set, including parameters  si=zi_ist
open_set = {}
params_thres = [0.01, 0.01, 0.01]
params_gap = [0.01, 0.01, 0.01]
# cnt_limit = 5
cnt_limit = 2


def build_open_set(open_set, closed_set, params_thres, params_gap, cnt_limit):
    for pam_val_hash, (pam_val, zi) in closed_set.items():

        # For each one-dimensional parameter, find n nodes within the nearby threshold range
        for idx, param in enumerate(params):

            # Expansion in both positive and negative directions
            for i in range(2):
                cnt = 0
                gap = params_gap[idx]

                # Expanding to a specified quantity or to a specified boundary has an impact on everything within the range
                while cnt < cnt_limit and gap <= params_thres[idx]:
                    new_pam_val = pam_val.copy()
                    new_pam_val[idx] += (gap if i == 0 else -gap)

                    new_pam_val_hash = hash(tuple(new_pam_val))
                    if new_pam_val_hash not in closed_set:
                        if new_pam_val_hash not in open_set:
                            open_set[new_pam_val_hash] = [new_pam_val, zi.copy()]
                            cnt += 1
                        else:
                            open_set[new_pam_val_hash][1].extend(zi.copy())
                    gap += params_gap[idx]


build_open_set(open_set, closed_set, params_thres, params_gap, cnt_limit)

# Select the topk with the largest si from the open collection
open_set_params = list(open_set.values())
import math

param_exp_dict = {}
for param in params + ['si', 'near_num', 'near_zi']:
    param_exp_dict[param] = []

for pam_val, zi_list in open_set_params:
    pam_val = [round(x, 3) for x in pam_val]
    for idx, param in enumerate(params):
        param_exp_dict[param].append(pam_val[idx])
    param_exp_dict['si'].append(np.average(zi_list))
    param_exp_dict['near_num'].append(len(zi_list))
    param_exp_dict['near_zi'].append(zi_list)
param_exp_pd = pd.DataFrame(param_exp_dict)
param_exp_pd.sort_values(by='si', ascending=False, inplace=True)
param_exp_pd.to_excel('./output/AgNC.xlsx', header=True, index=False)
param_exp_pd.head()

data.to_excel('./output/AgNCs.xlsx', header=True, index=False)
data.sort_values(by='wave_error', ascending=True, inplace=True)
data.head(100)