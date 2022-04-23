
from pypinyin import pinyin, Style

import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

import subprocess
import traci
import sumolib

def get_dir(in_dir):
    '''
    in_dir : 进口方向
    L_S_R_dir: 左、直、右
    '''
    if in_dir == '北':
        L_S_R_dir = ['东', '南', '西']
    elif in_dir == '东':
        L_S_R_dir = ['南', '西', '北']
    elif in_dir == '南':
        L_S_R_dir = ['西', '北', '东']
    else:
        L_S_R_dir = ['北', '东', '南']

    return L_S_R_dir


def get_flow_ID(inbound, outbound, index):
    hans = inbound + outbound
    tmp = pinyin(hans, style=Style.NORMAL, heteronym=False, errors='default', strict=True)
    res = tmp[0][0] + '_' + tmp[1][0] + '_' + str(index)
    
    return res


def pretty_xml(elem, level=0):
    '''
    增加换行符
    '''
    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            pretty_xml(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def gen_flow(data, time_range, rou_file):
    root = ET.Element('routes')       # 创建节点
    tree = ET.ElementTree(root)     # 创建文档

    for t in range(len(time_range)):
        # t = 0
        flow_t = data.loc[data['开始时间']==time_range[t], :] # 时间 筛选
        flow_t.index = np.arange(len(flow_t)) # reset the index

        for i in range(len(flow_t)): # 四个进口道方向
            flow_t_i = flow_t.iloc[i, :] # 每方向 开始生成流量

            inbound = flow_t_i.loc['进口道方向']
            # print(inbound)
            LSR_dir = get_dir(inbound) # 左、直、右
            LSR_fraction = np.array([0.2, 0.5, 0.3]) # 左、直、右
            LSR_color = ['1,0,0','0,1,0','0,0,1']
            # print(LSR_dir)
            LSR_num = flow_t_i.loc['过车流量/辆'] * LSR_fraction
            LSR_num = np.round(LSR_num).astype('int')
            # print(LSR_num)

            for j in range(len(LSR_dir)): # 三个转向 的流量
                element = ET.Element('flow')
                
                outbound = LSR_dir[j]
                flow_ID = get_flow_ID(inbound, outbound, index=t)  # ID
                
                b = t * (15*60) # begin
               
                e = (t+1) * (15*60)   # end
               
                fr = flow_t_i['O']  # from
                
                to = flow_t.loc[flow_t['进口道方向']==outbound, 'D'] # to
                to = to.iloc[0] # 有一个时数字了
                
                number = LSR_num[j] # number
                col = LSR_color[j]

                element.set('id', flow_ID)
                element.set('begin', str(b))
                element.set('end', str(e))
                element.set('from', str(fr))
                element.set('to', str(to))
                element.set('number', str(number))
                element.set('color', col)

                # element.text = ' '
                root.append(element)
                
    pretty_xml(root)          # 增加换行符
    tree.write(rou_file, encoding='utf-8', xml_declaration=True)


def gen_view_setting():
    view_file = 'map.view.xml'
    
    root = ET.Element('viewsettings')
    tree = ET.ElementTree(root)

    element = ET.Element('scheme')
    element.set('name',"real world" )
    root.append(element)

    element = ET.Element('delay')
    element.set('value', '50')
    root.append(element)

    pretty_xml(root)
    tree.write(view_file, encoding='utf-8', xml_declaration=True)


def start_sumo(rou_file, autoSim=True):

    sumocfg_file = rou_file.split(sep='.')[0] + '.sumocfg'
    sumo = sumolib.checkBinary('sumo')
    opts = [sumo,
            "-n", 'map.net.xml', 
            "-r",  rou_file,
            '--gui-settings-file','map.view.xml',
            "-e", "7200",
            "--step-length", "1",
            "--save-configuration", sumocfg_file,
            "--threads", "2",
            "--no-warnings", "true",
            "--start", 'true',
            "--duration-log.statistics",
            "--device.rerouting.adaptation-interval", "10",
            "--device.rerouting.adaptation-steps", "18",
            "-v", "--no-step-log",  
            "--ignore-route-errors", "true",
            "--collision.action", "none",]
    subprocess.call(opts)


    if autoSim: # GUI-界面打开sumo-gui运行
        sm = sumolib.checkBinary('sumo-gui')
        
        traci.start([sm, '-c', sumocfg_file])
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

        traci.close()


if __name__=='__main__':

    filename = '竹叶山流量-0418.xlsx'
    raw_data = pd.read_excel(filename, sheet_name='summary')

    data = raw_data.copy()

    zao_time =data.loc[0:7, '开始时间'].reset_index(drop=True)
    wan_time = data.loc[8:15, '开始时间'].reset_index(drop=True)

    zao_rou_file = 'map_zao.rou.xml'
    wan_rou_file = 'map_wan.rou.xml'

    gen_flow(data, zao_time, zao_rou_file)
    gen_flow(data, wan_time, wan_rou_file)

    gen_view_setting()
    
    rou_file = zao_rou_file
    rou_file = wan_rou_file

    start_sumo(rou_file, autoSim=True)
