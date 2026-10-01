#===============================================================================
# 参考脚本（原样收集 · 未验证 · 未运行）
# 来源文章: articles/20260930-用强大的GROMACS分析工具分析VASP的动力学结果.md
# 原文链接: https://mp.weixin.qq.com/s/pjLTG9KX1khrCx1pTW9B4w
# 用途    : 读 GROMACS 的 .xvg（含 @ title/xaxis/yaxis 元数据行）并用 matplotlib 画图
# 依赖    : Python + numpy + matplotlib
# 功能说明: references/tools.md 二.5（本目录只放源码文本，说明以那里为准）
# 抓取质量: 原网页把代码渲染成带行号的列表（行号粘在代码前），已**剥除行号**；缩进仍丢失。
#===============================================================================
import numpy as np
from matplotlib import pyplot as plt
import sys
import os
#------------------ FONT_setup ----------------------
font = {'family' : 'Arial',
'color' : 'black',
'weight' : 'normal',
'size' : 16.0,
 }
if len(sys.argv) <2:
#print(")
if sys.version[0]=='2':
 input=raw_input
 file=input("please with xvg file name-->")
else:
 file=sys.argv[1]
plt.style.use("ggplot")
ifnot os.path.exists(file):
 print("No file exists")
 sys.exit(0)
data=[]
with open(file,'r') as reader:
for index,line in enumerate(reader):
if"title"in line:
 title = eval(' '.join(line.split()[2:]))
elif"xaxis"in line and"label"in line:
 xlabel=eval(' '.join(line.split()[3:]))
elif"yaxis"in line and"label"in line:
 ylabel=eval(' '.join(line.split()[3:]))
elif ((not line.startswith("@")) and (not line.startswith("&"))\
and (not line.startswith("#"))):
 data.append(list(map(float,line.split())))
datas=np.array(data)
plt.plot(datas[:,0],datas[:,1:])
plt.ylabel(ylabel,fontdict=font)
plt.xlabel(xlabel,fontdict=font)
plt.xticks(fontsize=font['size']-3)
plt.yticks(fontsize=font['size']-3)
plt.title(title,fontdict=font)
plt.show()
