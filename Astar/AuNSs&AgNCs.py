import random
import math

#Calculate valuation function
# w1，w2，w3
#Peak position, peak ratio, peak width
# 2nd_peak_wave, 2nd_peak_ratio, 2nd_peak_width
#Only consider the peak positio

def get_zi_func(x, MAX_VALUE=1):
    
    # Normalization
    z = 1.0 - (x / MAX_VALUE)
    
    return z

def get_target_zi_func(x, TARGET_PEAK=0, MAX_VALUE=50):
    
    # Normalization closest to the target
    z = 1 - (abs(x - TARGET_PEAK)/MAX_VALUE)
    
    return z

'''
    Minimum error in small-sized Au NSs curves
'''
def small_size_filer(x):
    if re.findall(r'小尺寸AuNSs_', x['day']):
        return True
    else:
        return False
    
'''
    Minimum error in large-sized curves
'''
def big_size_filer(x):
    if re.findall(r'大尺寸AuNSs_', x['day']):
        return True
    else:
        return False

'''
    Minimum error in peak position at polyhedral curve
'''
def polyhedron_filer(x):
    if re.findall(r'多面体AuNSs_', x['day']) and re.findall(r'A', x['wave']):
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
            
def choose_topk_params(open_set, col='si', topk=10):
    # Select the topk with the highest si from the open set
    open_set_params = list(open_set.values())
    import math
    param_exp_dict = {
        '10mM HAuCl4.1': [],
        '0.1M AA': [],
        'T/℃.1': [],
        'Seed':[],
        '10mM HAuCl4.2'[],
        'AA.2'[],
        'T/℃.2': [],
        'si': [],
        'near_num': [],
        'near_zi': []
    }
    for pam_val, zi_list in open_set_params:
        pam_val = [round(x, 3) for x in pam_val]
        for idx, param in enumerate(params):
            param_exp_dict[param].append(pam_val[idx])
        param_exp_dict['si'].append(np.average(zi_list))
        param_exp_dict['near_num'].append(len(zi_list))
        param_exp_dict['near_zi'].append(zi_list)
    param_exp_pd = pd.DataFrame(param_exp_dict)
    param_exp_pd.sort_values(by=col, ascending=False, inplace=True)
    return param_exp_pd.head(topk)
# Workflow
if __name__ == '__main__':

    # Filter experimental data
    data = data_param_wave[data_param_wave.apply(big_size_filer, axis=1)].reset_index(drop=True)

    # construct closed_set
    target_col = 'peak_error'
    params = ['Seed','10mM HAuCl4.1','0.1M AA', 'T/℃.1','10mM HAuCl4.2' , 'AA.2', 'T/℃.2',]
    #AgNCs parameters: ['Seed','AgNO3','0.1M AA', 'CF3COOAg', 'T/℃.',]
    closed_set = {}
    build_closed_set(closed_set, data, params, target_col)

    # construct open_set
    open_set = {}
    params_gap = [0.01, 0.01, 0.01, 3, 0.01, 0.01, 4]
    params_gap_thres = [0.02, 0.04, 0.05,3, 0.04, 0.04, 2]
    params_cnt_limit = 4
    params_near_gap = [0.01, 0.01, 0.01, 1, 0.02, 0.02, 1]
    params_near_thres = [0.01, 0.02, 0.01,3, 0.02, 0.01, 2]
    build_open_set(open_set, closed_set)

    # Select parameters for valuation topk
    param_exp_pd = choose_topk_params(open_set)
    param_exp_pd.to_excel('./output/param_exp_big.xlsx', header=True, index=False)

    # Conduct experiments and update experimental data
    build_expiriment_and_update(param_exp_pd)