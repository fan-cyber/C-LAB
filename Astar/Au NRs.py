import random
import math

#Calculate valuation function
# w1，w2，w3
#Peak position, peak ratio, peak width
# 2nd_peak_wave, 2nd_peak_ratio, 2nd_peak_width
#Only consider the peak position

# Calculate the peak position estimation function
def get_target_zi_func(x, TARGET_PEAK=0, MAX_VALUE=1000):
    
    # Normalization closest to the target
    z = 1 - (abs(x - TARGET_PEAK)/MAX_VALUE)
    
    return z

'''
    Au NRs
'''
def data_filer(x):
    if re.findall(r'金纳米棒_', x['day']):
        return True
    else:
        return False


# Build the initial closed set (including newly completed experiments), objectives, including parameters, and a list of zi
def build_closed_set(closed_set, data, params, target_col):
    for i in range(len(data)):
        zi = get_target_zi_func(data.loc[i, target_col])
        param_list = data.loc[i, params].values
        param_list_hash = hash(tuple(param_list))
        if param_list_hash not in closed_set:
            closed_set[param_list_hash] = (param_list, [zi])
        else:
            closed_set[param_list_hash][1].append(zi)


# Construct an initial subset set based on the closed set as the open set, including parameters, si=zi_list
def build_open_set(open_set, closed_set):
    for pam_val_hash, (pam_val, zi) in closed_set.items():
        
        # For each one-dimensional parameter, find n nodes within the nearby threshold range
        for idx, param in enumerate(params):
            
            # Expanding in both positive and negative directions
            for i in range(2):
                cnt = 0
                gap = params_gap[idx]

                # Expanding to a specified quantity or boundary has an impact on the scope
                while cnt < params_cnt_limit and gap <= params_gap_thres[idx]:
                    new_pam_val = pam_val.copy()
                    new_pam_val[idx] += (gap if i == 0 else -gap)
                    
                    if new_pam_val[idx]<=0:
                        break
                    
                    new_pam_val_hash = hash(tuple(new_pam_val))
                    if new_pam_val_hash not in closed_set and new_pam_val_hash not in open_set:
                        open_set[new_pam_val_hash] = [new_pam_val, []]
                        cnt += 1
                    gap += params_gap[idx]
                    
            # Update in both positive and negative directions
            for i in range(2):
                gap = params_near_gap[idx]

                # Expanding to the specified boundary has an impact on all within the scope
                while gap <= params_near_thres[idx]:
                    new_pam_val = pam_val.copy()
                    new_pam_val[idx] += (gap if i == 0 else -gap)
                    
                    new_pam_val_hash = hash(tuple(new_pam_val))
                    if new_pam_val_hash not in closed_set and new_pam_val_hash in open_set:
                        open_set[new_pam_val_hash][1].extend(zi.copy())
                    gap += params_near_gap[idx]
            
def choose_topk_params(open_set, step, col='si_ucb', topk=10, alpha=0.1):
    # Select the topk with the highest si from the open set
    open_set_params = list(open_set.values())
    import math
    param_exp_dict = {
        '3.6542M HCl/mL': [],
        '4mM AgNO3/mL': [],
        'Seed/mL': [],
        'si': [],
        'si_ucb': [],
        'near_num': [],
        'near_zi': []
    }
    for pam_val, zi_list in open_set_params:
        pam_val = [round(x, 3) for x in pam_val]
        for idx, param in enumerate(params):
            param_exp_dict[param].append(pam_val[idx])
        si = np.average(zi_list)
        si_ucb = si + alpha * math.sqrt(2.0 * math.log(step) / len(zi_list))
        param_exp_dict['si'].append(si)
        param_exp_dict['si_ucb'].append(si_ucb)
        param_exp_dict['near_num'].append(len(zi_list))
        param_exp_dict['near_zi'].append(zi_list)
    param_exp_pd = pd.DataFrame(param_exp_dict)
    param_exp_pd.sort_values(by=col, ascending=False, inplace=True)
    return param_exp_pd.head(topk)
# Workflow
if __name__ == '__main__':

    step = 1
    MAX_STEP = 100
    target = 800
    target_thres = 10
    data_param_wave = pd.read_excel('./data/data_param.xlsx', header=0)
    while step < MAX_STEP:
         # Filter experimental data
        data = data_param_wave[data_param_wave.apply(data_filer, axis=1)].reset_index(drop=True)

        # construct closed_set
        target_col = '2nd_peak_wave'
        params = ['3.6542M HCl/mL', '4mM AgNO3/mL','Seed/mL' ]
        closed_set = {}
        build_closed_set(closed_set, data, params, target_col)

        # contruct open_set
        open_set = {}
        params_gap = [0.02, 0.02, 0.02]
        params_gap_thres = [0.06, 0.06, 0.06]
        params_cnt_limit = 6
        params_near_gap = [0.01, 0.01, 0.01]
        params_near_thres = [0.03, 0.03, 0.01]
        build_open_set(open_set, closed_set)

        # Select parameters for valuation topk
        param_exp_pd = choose_topk_params(open_set)

        # Conduct experiments and update experimental data
        build_expiriment_and_update(data_param_wave, param_exp_pd)

        # Detected a distance error of 10nm from the target, algorithm completed
        if check_target(data_param_wave, target, target_col, target_thres):
            data_param_wave.to_excel('./output/data_param_finish.xlsx', header=True, index=False)
            break

        step += 1