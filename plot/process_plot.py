

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import optparse
import sys

plt.rcParams["font.sans-serif"]=["SimHei"] #设置字体
plt.rcParams["axes.unicode_minus"]=False #该语句解决图像中的“-”负号的乱码问题

def get_options(args=None):
    optParser = optparse.OptionParser()
    optParser.add_option('-t', '--fig-type', dest='figtype',
                    default='edge_density', help="执行画什么图")
    optParser.add_option('-s', '--scheme', dest='scheme', 
                    default="优化后-方案2", help="优化后的方案几,用于legend")
    options, args = optParser.parse_args(args=args)
    
    lab_dict = dict(
                edge_arrived="到达车辆(辆)",
                edge_density= "路段密度(辆/千米)",
                edge_laneDensity="车道密度(辆/千米/车道)", 
                edge_occupancy="占有率(%)",
                edge_timeLoss= "损失时间(秒)",
                edge_speed = "平均速度(米/秒)",
                edge_traveltime="通过时间(秒)",
                edge_waitingTime="停车排队时间(秒)",
                edge_entered="进入车辆数(辆)"
                    )
    
    if options.figtype not in lab_dict.keys():
        print("麻烦您换一个指标，咱们没有这个数据")
        sys.exit()

    return options


def data_process(filename, pos):
    '''
    filename: 读取的csv文件,  分隔符号是;
    pos: 需要晒出的位置
    '''
    data= pd.read_csv(filename, sep=";")
    tmp = data[data['edge_id'].isin(pos)]
    tmp.reset_index(drop=True, inplace=True)
    
    tmp.drop(labels=["interval_id","edge_id"], axis=1, inplace=True)
    tmp = tmp.groupby(by=["interval_begin"]).mean()
    res = tmp.reset_index() # 分组用的"interval_begin" 加进去了

    idx = np.array(res["interval_begin"])/120
    res.index = idx.astype(int)

    return res


def plot_fig(data_be, data_af, fig_type, prefix, after_legend):
    '''
    data_be: 处理好的优化 前 的数据
    data_df: 处理好的优化 后 的数据
    fig_type: 用那列数据画图
    pos_prefix: 画图的标题开头的数据
    '''
    lab_dict = dict(
                edge_arrived="到达车辆(辆)",
                edge_density= "路段密度(辆/千米)",
                edge_laneDensity="车道密度(辆/千米/车道)", 
                edge_occupancy="占有率(%)",
                edge_timeLoss= "损失时间(秒)",
                edge_speed = "平均速度(米/秒)",
                edge_traveltime="通过时间(秒)",
                edge_waitingTime="停车排队时间(秒)",
                edge_entered="进入车辆数(辆)"
                    )                  
    y_label = lab_dict[fig_type]

    x1 = np.array(data_be.index)
    x2 = np.array(data_af.index)

    y1 = data_be[fig_type]
    y2 = data_af[fig_type]

    fig = plt.figure(dpi=150)
    plt.plot(x1, y1, label='优化前', marker = 'o')
    plt.plot(x2, y2, label=after_legend, marker = 'o')

    plt.xlabel('时间(每2分钟)', fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    
    fig_title = prefix +":"+ fig_type.split(sep='_')[1].title()
    plt.title(fig_title)
    
    plt.legend()
        
    plt.savefig(after_legend+"-"+ fig_type.split(sep='_')[1].title() + "-"+prefix + '.png' )


def main(options, file_before, file_after):

    edges =dict(
        huan= ["331159366#1","331159366#2","331159366#3","331159366#4","331159366#5" ,"331159366#6","331159366#7","331159366#8"],
        dong = ["331159364#2.1476" , "331159364#2.526"],
        nan = ["826105809#14","826105809#14.186","826105809#14.238"],
        xi = ["331158296#2", "331158296#2.100", "331158296#2.118"],
        bei = ["897570587", "897570587.118", "897570589"],
        xi2 = ["331158298", "331158298.105"]
        )
    
    fig_type = options.figtype
    for pre, pos in edges.items():
        pre_dict= dict(
                        huan="圆环",
                        dong="东进口车道",
                        xi="西进口车道",
                        xi2 ="西出口车道",
                        nan="南进口车道",
                        bei="北进口车道"
                    )
        prefix = pre_dict[pre]

        data_be = data_process(file_before, pos)
        data_af = data_process(file_after, pos)
        
        # 打印出来，查看一下为啥报错
        # data_be.to_excel('res'+ pre +"-"+'before'+ ".xlsx")
        # data_af.to_excel('res'+ pre +"-"+'after'+ ".xlsx")

        after_legend = options.scheme
        plot_fig(data_be, data_af, fig_type, prefix, after_legend)


if __name__ == '__main__':

    # 一个流程，全部跑通
    lab_dict = dict(
                edge_arrived="到达车辆(辆/两分钟)",
                edge_density= "路段密度(辆/千米)",
                edge_laneDensity="车道密度(辆/千米/车道)", 
                edge_occupancy="占有率(%)",
                edge_timeLoss= "损失时间(秒)",
                edge_speed = "平均速度(米/秒)",
                edge_traveltime="通过时间(秒)",
                edge_waitingTime="停车排队时间(秒)",
                edge_entered="进入车辆数(辆)"
                    )
    

    file_before = 'edata_2min_agg_before.csv'
    
    
    #! 方案二，对比
    file_after2 = 'edata_2min_agg_after2.csv'
    for val in lab_dict.keys():
        args = ['-s', "优化后-方案2"]
        args.append('-t')
        args.append(val)
        
        # print(args)

        options = get_options(args)
        main(options, file_before, file_after2)


    #! 方案一，对比
    file_after1 = 'edata_2min_agg_after1.csv'
    for val in lab_dict.keys():
        args = ['-s', "优化后-方案1"]
        args.append('-t')
        args.append(val)
        
        # print(args)

        options = get_options(args)
        main(options, file_before, file_after1)

