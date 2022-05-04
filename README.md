# 武汉——交叉口拥堵溯源分析

> 研究环形交叉口：[武汉大道-二环路交叉-竹叶山环交](https://map.baidu.com/@12723399.279562738,3562867.438120239,19.82z)
>
> 分析拥堵情况，进行拥堵溯源分析
>
> 下面是一些关键修改节点和思路的记录

## V1需求：实现一个简单的可视化就好

- 新增内容：
  - OSM导入路网，修改交叉口线性设计
  
    ```
    生成路网
    netconvert --osm-files map.osm --output-file map.net.xml 
    netconvert --osm-files map.osm --output-file map.net.xml --ramps.guess True
    ```
  
  - 添加流量，还是写一个代码吧，不然修改太麻烦了`flow_gen.py`
  
  - 仅保留研究交叉口及附近的路网即可，其他删掉

## V2需求：保留所有的路网比较好看

- 利用Git命令恢复信息

- 修改可视化的额问题，添加poi文件和gui-setting的

  ```
  生成POI文件
  polyconvert -n map.net.xml --osm-files map.osm -o map.poi.xml
  ```

  

## V3：增加一部分的掉头车辆

- 添加一部分的掉头车辆
- 修改代码实现`flow_gen.py`

## V4：和甲方汇报后，新增需求

> 主要内容是通过给数据的那个交叉口做拥堵溯源，简单的分析
>
> 然后提一些简单的方案，怎么缓解，
>
> 可以先梳理一下数据需求我问他们要，比如增加一些新的交通流数据？



- 任务需求：
  - 三个主要任务：
    1. 仿真还原现状拥堵 
    2. 拥堵溯源分析+可视化图表
    3. 管控措施仿真，对比前后效果


- **任务1**：修改内容：

  1. 增加周边四个关键交叉口的：几何设计、信号、流量

  2. 修改研究交叉口的流量生成和消失点

     <img src="figure/研究交叉口及周边主要交叉口.png" style="zoom: 55%;" />

  3. 修改了研究交叉口的 东进口的流量起始edge

  

- **任务2**：


  - 研究内容

    1.  **拥堵点**：环交北到西方向（西出口到相邻交叉口的拥堵导致

  - 思考内容

    1. 还是避免不了，手动输入一部分流量
    2. 周边四个交叉口的流量就直接手动添加【`map_manual.rou.xml`

  - 增加四个交叉口的的流量：

- 2北：

  |  东  |  南  |  西  |  北  |
  | :--: | :--: | :--: | :--: |
  | 1200 | 800  | 300  | 800  |



- 3西：

  |  东  |  南  |  西  |  北  |
  | :--: | :--: | :--: | :--: |
  | 600  |      | 500  | 700  |



- 4南：

  |  东  |  南  |  西  |  北  |
  | :--: | :--: | :--: | :--: |
  | 1300 | 1500 | 1400 | 1200 |



- 5东：

  |  东  |  南  |  西  |  北  |
  | :--: | :--: | :--: | :--: |
  | 400  | 300  | 300  | 400  |