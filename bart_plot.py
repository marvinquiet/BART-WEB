# -*- coding: utf-8 -*-
import os, sys
# plot bart
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# TODO: should be packaged as python bart_plot.py -> and write into slurm

# stat: score
# tfs: tf_name list
# ID: target tf
# args: related to outputdir
# col: r_rank
def stat_plot(stat, tfs, ID, bart_output_dir):
    # box-plot
    fig=plt.figure(figsize=(4,4))
    # default --nonorm=FALSE
    # plt.boxplot([stat.loc[i]['tf_score'] for i in stat.index])
    # plt.scatter(1,stat.loc[ID]['tf_score'],c='r',marker='o',s=60)

    plt.boxplot([stat.loc[i]['r_rank'] for i in stat.index])
    plt.scatter(1,stat.loc[ID]['r_rank'],c='r',marker='o',s=60)

    plt.gca().invert_yaxis()
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.title(ID,fontsize = 12)
    plt.ylabel('Rank Score',fontsize = 12)
    # plotdir = bart_output_dir + os.sep + '{}_plot'.format(args.ofilename)
    plotdir = bart_output_dir + '/plot'

    #os.makedirs(plotdir,exist_ok=True)
    try:
        os.makedirs(plotdir,exist_ok=True)
    except:
        sys.exit('Output directory: {} could not be created.'.format(plotdir))
    figname1 = plotdir+os.sep+'{}_avg_z_p_boxplot'.format(ID)
    plt.savefig(figname1,bbox_inches='tight')
    plt.close()    
    
    
    #Cumulative Fraction plot
    background = []
    for tf in tfs:
        background.extend(tfs[tf])
    target = tfs[ID]       
    background = sorted(background)
    fig=plt.figure(figsize=(4,4))   
    dx = 0.01
    x = np.arange(0,1,dx)       
    by,ty = [],[]      
    for xi in x:
        by.append(sum(i< xi for i in background )/len(background))
        ty.append(sum(i< xi for i in target )/len(target))
    plt.plot(x,by,'b-',label='ALL') 
    plt.plot(x,ty,'r-',label='{}'.format(ID)) 
    plt.legend()
    #maxval = max(background)
    #minval = min(background)
    #plt.ylim([0,1])
    #plt.xlim([0,1])
    plt.ylabel('Cumulative Fraction',fontsize=12)
    plt.xlabel('AUC',fontsize=12)
    figname2 = plotdir+os.sep+'{}_cumulative_distribution'.format(ID)
    plt.savefig(figname2,bbox_inches='tight')
    plt.close()


def plot_top_tf(bart_table_df, bart_output_dir, AUCs):
    # top 20 for each column, get intersection
    top_cnt = round(len(bart_table_df.index)/5)

    tf_score_list = set(bart_table_df.sort_values(by=['tf_score'], ascending=False).head(top_cnt).index.values)
    z_score_list = set(bart_table_df.sort_values(by=['z_score'], ascending=False).head(top_cnt).index.values)
    max_auc_list = set(bart_table_df.sort_values(by=['max_auc'], ascending=False).head(top_cnt).index.values)
    p_value_list = set(bart_table_df.sort_values(by=['p_value']).head(top_cnt).index.values)
    r_rank_list = set(bart_table_df.sort_values(by=['r_rank']).head(top_cnt).index.values)
    sets = [tf_score_list, z_score_list, max_auc_list, p_value_list, r_rank_list]

    # which needs to be plot
    tf_intersection = list(set.intersection(*sets))
    
    # get tfs with all AUCs
    tfs = {}
    for tf_key in AUCs.keys():
        tf = tf_key.split('_')[0]
        auc = AUCs[tf_key]
        if tf not in tfs:
            tfs[tf] = [auc]
        else:
            tfs[tf].append(auc)

    for ID in tf_intersection:
        stat_plot(bart_table_df, tfs, ID, bart_output_dir)



def get_AUCs(auc_file):
    AUCs = {}
    with open(auc_file, 'r') as fopen:
        for line in fopen:
            tf_key, auc_equation = line.strip().split('\t')
            auc = float(auc_equation.replace(' ', '').split('=')[1])
            AUCs[tf_key] = auc
    return AUCs

def main():
    # example: python bart_plot.py user_key
    # print (sys.argv)

    # get argv
    script_name = sys.argv[0]  
    user_key = sys.argv[1] # user_key is needed
    
    import do_process
    user_data = do_process.get_user_data(user_key)
    user_path = user_data['user_path']

    bart_result_file = ''
    bart_auc_file = ''
    auc_result_dict = {}

    bart_title = ['tf_name', 'tf_score', 'p_value', 'z_score', 'max_auc', 'r_rank'] 
    bart_output_dir = os.path.join(user_path, 'download/bart_output')

    bart_auc_ext = '_auc.txt'
    for root, dirs, files in os.walk(bart_output_dir):
        for bart_file in files:
            if bart_auc_ext in bart_file:
                bart_auc_file = os.path.join(root, bart_file)
                user_file_name = bart_file.strip(bart_auc_ext)
                auc_result_dict[user_file_name] = {}
                auc_result_dict[user_file_name]['auc'] = bart_auc_file

    bart_res_ext = '_bart_results.txt'     
    for root, dirs, files in os.walk(bart_output_dir):
        for bart_file in files:
            if bart_res_ext in bart_file:
                bart_result_file = os.path.join(root, bart_file)
                user_file_name = bart_file.strip(bart_res_ext)
                if user_file_name not in auc_result_dict:
                    auc_result_dict[user_file_name] = {}
                    # something definitely went wrong if no _auc.txt files!
                    # the plot can not be plotted!!
                    # only the statistics will be shown!
                auc_result_dict[user_file_name]['res'] = bart_result_file

    for user_file_name, bart_files in auc_result_dict.items():
        bart_auc_file = bart_files['auc']
        bart_result_file = bart_files['res']
        AUCs = get_AUCs(bart_auc_file)
        bart_df = pd.read_csv(bart_result_file, sep='\t', names=bart_title[1:], index_col=0, skiprows=1)
        plot_top_tf(bart_df, bart_output_dir, AUCs)

if __name__ == '__main__':
    main()