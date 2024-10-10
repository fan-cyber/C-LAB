import random
import math

# Algorithm begins
# The close set is empty
# The open set is empty


DEFAULT_VALUE = 20


def init(data, n=3, target=850, thres=100):
    data.loc[:, 'is_close'] = 0
    data.loc[:, 'is_open'] = 0
    data.loc[:, 'zi'] = 0
    data.loc[:, 'sn'] = 0
    data.loc[:, 'si'] = 0
    data.loc[:, 'si_ucb'] = 0
    data.loc[:, 'step'] = -1
    # Select the starting point for the experiment and add it to the open set
    t_data = data[(data['2nd_peak_wave'] > target - thres) & (data['2nd_peak_wave'] < target + thres)]
    t_index = random.sample(t_data.index.to_list(), min(n, len(t_data)))
    print("init:", t_index, t_data.index.to_list())
    for p in t_index:
        data.loc[p, 'is_open'] = 1
        data.loc[p, 'si'] = DEFAULT_VALUE
        data.loc[p, 'si_ucb'] = DEFAULT_VALUE


# Calculate valuation function
# w1，w2，w3
# LSPR，Peak ratio，FWHM
# 2nd_peak_wave, 2nd_peak_ratio, 2nd_peak_fwhm
# Only consider Peak ratio

def get_zi_func(x, MAX_VALUE=4.0):
    # Normalization
    z = x / MAX_VALUE

    return z


def check_is_init(data, idx):
    return data.loc[idx, 'si_ucb'] == DEFAULT_VALUE


# Construct  sub set
# At the beginning, we used a large step delta and adaptive construction, with a fixed number of up and down selections
# AgNO3 HCl Seed
def update_func(data, idx, ch_zi):
    if not check_is_init(data, idx):
        data.loc[idx, 'is_open'] = 1
        data.loc[idx, 'si'] = data.loc[idx, 'si'] * data.loc[idx, 'sn'] + ch_zi
        data.loc[idx, 'sn'] += 1
        data.loc[idx, 'si'] /= data.loc[idx, 'sn']
        print(f"idx={idx} si={data.loc[idx, 'si']} sn={data.loc[idx, 'sn']}")


def update_ucb_func(data, step, alpha=0.1):
    print(f"open set:{data[data['is_open'] == 1].index.values}")
    for idx in data[data['is_open'] == 1].index.values:
        if not check_is_init(data, idx):
            data.loc[idx, 'si_ucb'] = data.loc[idx, 'si'] + alpha * math.sqrt(
                2.0 * math.log(step) / data.loc[idx, 'sn'])


def build_sub_and_update(data, ch, target, step, delta_cnt=5, HCL_thres=0.06, AgNO3_thres=0.06):
    print("[Sub & Open Update] ************")
    cnt = 0
    for ch_idx in ch.index.values:
        idx = ch_idx - 1
        ch_zi = data.loc[ch_idx, 'zi']
        while cnt < delta_cnt and idx >= 0 \
                and abs(data.loc[idx, '3.6542M 盐酸/mL'] - ch.loc[ch_idx, '3.6542M 盐酸/mL']) < HCL_thres \
                and abs(data.loc[idx, '4mM AgNO3/mL'] - ch.loc[ch_idx, '4mM AgNO3/mL']) < HCL_thres:

            if data.loc[idx, 'is_close'] == 0:
                update_func(data, idx, ch_zi)
                cnt += 1
            idx -= 1
        cnt = 0
        idx = ch_idx + 1
        while cnt < delta_cnt and idx < len(data) \
                and abs(data.loc[idx, '3.6542M 盐酸/mL'] - ch.loc[ch_idx, '3.6542M 盐酸/mL']) < HCL_thres \
                and abs(data.loc[idx, '4mM AgNO3/mL'] - ch.loc[ch_idx, '4mM AgNO3/mL']) < HCL_thres:

            if data.loc[idx, 'is_close'] == 0:
                update_func(data, idx, ch_zi)
                cnt += 1
            idx += 1
    update_ucb_func(data, step)
    print("")


def get_max_si_from_open(data, col='si', topk=1):
    print("[Choose data form Open] **********")

    open_set = data[data['is_open'] == 1]

    ch_index = open_set.sort_values([col], ascending=False).head(topk).index.values

    data_ch = data.loc[ch_index, :]
    print(f"idx={data_ch.index.values}, {col}={data_ch[col].values}")
    print("")

    return data_ch


def build_experiment(data, ch, step, target):
    print("[Build Experiment] ************")

    data.loc[data_ch.index.values, 'is_open'] = 0
    data.loc[data_ch.index.values, 'is_close'] = 1
    data.loc[data_ch.index.values, 'step'] = int(step)

    for idx in data_ch.index.values:
        data.loc[idx, 'zi'] = get_zi_func(data.loc[idx, '2nd_peak_ratio'])

    print(
        f"si_ucb={ch['si_ucb'].values}, si={ch['si'].values}, real={ch['2nd_peak_wave'].values}, is_close={data.loc[data_ch.index.values, 'is_close'].values}")
    print("")
    return ch['2nd_peak_wave'].values


# for target in [600, 650, 700, 750, 800, 850, 900]:
for target in [700]:
    final_step = 15
    for i in range(200):
        step = 1
        flag = False
        MAX_STEP = 100
        MAX_THRES = 10
        DELTA_CNT = 5
        HCL_thres = 0.06
        AgNO3_thres = 0.06
        init(data, 3, target, 10)
        while step < MAX_STEP and data['is_open'].sum() > 0:
            print(f"[STEP {step}] ---------------")

            # Select the point with the largest si from the open set
            data_ch = get_max_si_from_open(data, 'si_ucb', 1)

            # Conduct experiments to obtain real results
            real_peak_wave = build_experiment(data, data_ch, step, target)

            # Update the si corresponding to the sub set
            build_sub_and_update(data, data_ch, target, step, DELTA_CNT, HCL_thres, AgNO3_thres)

            step += 1
            print("")
        if step > final_step:
            final_step = step
            data[data['is_close'] == 1].sort_values(by='step', ascending=True).to_excel(
                f'./output/Astar_rate_{target}.xlsx', header=True, index=False)

tdata = pd.read_excel('./output/Astar.xlsx', header=0)
tdata[['4mM AgNO3/mL',
       '3.6542M 盐酸/mL',
       '晶种/mL', 'wave_name', 'label', 'peak_num',
       '2nd_peak_wave', '2nd_peak_width', '2nd_peak_ratio', '2nd_peak_diff',
       'is_close', 'is_open', 'sn', 'si', 'step', 'zi', 'si_ucb']].head(60)
