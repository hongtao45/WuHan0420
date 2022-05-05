
from pypinyin import pinyin, Style

import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

import optparse
import subprocess
import traci
import sumolib
import sys

def get_options(args=None):
    optParser = optparse.OptionParser()
    optParser.add_option("-p", "--peak", dest="peak", default='zao',
                        help="指定运行早晚高峰的哪一个代码")
    optParser.add_option('-a', '--auto-sim', dest='autoSim', default=True, 
                        action="store_false", help="是否直接打开sumo-gui")
    optParser.add_option("-c", "--sumocfg", dest="sumocfg", default=False, 
                        action="store_true", help="是否生成新的sumocfg文件")
    optParser.add_option("-f", "--flow", dest="flow", default=False,
                        action="store_true", help="重新生成流量")

    (options, args) = optParser.parse_args(args=args)
    return options


def get_dir(in_dir):
    '''
    input:
        in_dir : 进口方向
    output:
        LSR_dir: 进口方向的三个转向方向：[左、直、右、掉头]
    '''
    if in_dir == '北':
        LSR_dir = ['东', '南', '西', '北']
    elif in_dir == '东':
        LSR_dir = ['南', '西', '北', '东']
    elif in_dir == '南':
        LSR_dir = ['西', '北', '东', '南']
    else:
        LSR_dir = ['北', '东', '南', '西']

    return LSR_dir


def get_flow_ID(inbound, outbound, index):
    '''
    根据进口道和出口到方向,生成flow 的id
    '''
    hans = inbound + outbound
    tmp = pinyin(hans, style=Style.NORMAL, heteronym=False, errors='default', strict=True)
    res = tmp[0][0] + '_' + tmp[1][0] + '_' + str(index)
    
    return res


def pretty_xml(elem, level=0):
    '''
    XML 文档写入文件的时候
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
    '''
    生成流量
    并保存到文件中
    '''
    root = ET.Element('routes')       # 创建节点
    tree = ET.ElementTree(root)     # 创建文档

    for t in range(len(time_range)):
        # t = 0
        flow_t = data.loc[data['开始时间']==time_range[t], :] # 时间 筛选
        flow_t.index = np.arange(len(flow_t)) # reset the index
        # flow_t = data.loc[data['开始时间']==time_range[t], :].reset_index(drop= True)

        for i in range(len(flow_t)): # 四个进口道方向
            flow_t_i = flow_t.iloc[i, :] # 每方向 开始生成流量

            inbound = flow_t_i.loc['进口道方向']
            # print(inbound)
            LSR_dir = get_dir(inbound) # 左、直、右、掉头
            LSR_fraction = np.array([0.2, 0.5, 0.3, 0.05]) # 左、直、右、掉头
            LSR_color = ['1,0,0', '0,1,0', '0,0,1', '1,0,0']
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
                element.set('departLane', 'best')

                # element.text = ' '
                root.append(element)
                
    pretty_xml(root)          # 增加换行符
    tree.write(rou_file, encoding='utf-8', xml_declaration=True)


def gen_view_setting():
    '''
    生成一个gui-setting的文件
    '''
    view_file = 'map.view.xml'
    
    root = ET.Element('viewsettings')
    tree = ET.ElementTree(root)

    element = ET.Element('scheme')
    element.set('name',"real world" )
    root.append(element)

    element = ET.Element('delay')
    element.set('value', '50')
    root.append(element)

    element = ET.SubElement(root, 'viewport')
    # element = ET.Element('viewport')
    element.set('zoom','3400.39')
    element.set('x','16165.49')
    element.set('y','14642.71')
    element.set('angle','0')
    # root.append(element)

    pretty_xml(root)
    tree.write(view_file, encoding='utf-8', xml_declaration=True)


def start_sumo(rou_file, options):
    '''
    生成sumocfg文件
    自动打开运行sumo-gui
    '''
    autoSim = options.autoSim
    sumocfg = options.sumocfg
    
    sumocfg_file = rou_file.split(sep='.')[0] + '.sumocfg'
    
    if sumocfg:
        
        sumo = sumolib.checkBinary('sumo')
        opts = [sumo,
                "-n", 'map.net.xml', 
                "-r",  ','.join([rou_file, 'map_manual.rou.xml']),
                "-a", ','.join(["map.add.xml", "edgedata.add.xml"]),
                '--gui-settings-file','map.view.xml',
                "-e", "7200",
                "--step-length", "1",
                "--save-configuration", sumocfg_file,
                "--threads", "2",
                "--no-warnings", "true",
                "--start", 'true',
                "--duration-log.statistics",
                "--device.rerouting.adaptation-interval", "20",
                "--device.rerouting.adaptation-steps", "30",
                "-v", "--no-step-log",  
                "--ignore-route-errors", "true",
                "--collision.action", "none"]
        subprocess.call(opts)


    if autoSim: # GUI-界面打开sumo-gui运行
        sm = sumolib.checkBinary('sumo-gui')
        
        traci.start([sm, '-c', sumocfg_file])
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

        traci.close()


if __name__=='__main__':

    zao_args = ['-p','zao','-a','true'] 
    wan_args = ['-p','wan','-a','true'] 
    
    #! options = get_options(zao_args) 
    # options = get_options(wan_args)  #! 需要展示晚高峰时，注释掉这一行
    
    options = get_options()
    
    filename = '竹叶山流量-0418.xlsx'
    
    zao_rou_file = 'map_zao.rou.xml'
    wan_rou_file = 'map_wan.rou.xml'
    
    if options.flow:
        raw_data = pd.read_excel(filename, sheet_name='summary')

        data = raw_data.copy()

        zao_time =data.loc[0:7, '开始时间'].reset_index(drop=True)
        wan_time = data.loc[8:15, '开始时间'].reset_index(drop=True)


        gen_flow(data, zao_time, zao_rou_file)
        gen_flow(data, wan_time, wan_rou_file)

    #! 生成新的 显示界面的配置文件
    # gen_view_setting()
    
    #! 选择运行的时间
    if 'zao' in options.peak: # 运行早高峰的仿真
        start_sumo(zao_rou_file, options)
    elif 'wan' in options.peak:
        start_sumo(wan_rou_file, options)
    else:
       sys.exit(1)
