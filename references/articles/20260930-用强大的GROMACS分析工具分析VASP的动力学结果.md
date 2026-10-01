# 用强大的GROMACS分析工具分析VASP的动力学结果

- 来源: `https://mp.weixin.qq.com/s/pjLTG9KX1khrCx1pTW9B4w`
- 类型: html (url)
- 抓取时间: 2026-09-30 23:27:33
- 作者: Tamas
- 标签: AIMD, GROMACS, 轨迹分析, 微信文章
- 正文字数: 4605

---
# 用强大的GROMACS分析工具分析VASP的动力学结果

OriginalTamasTamas 学术之友

在小说阅读器读本章

去阅读

在公众号小说中沉浸阅读

之前的教程里我们介绍了一个XDATCAR_toolkit.py工具，将VASP的AIMD的轨迹转成PDB的格式，再借用VMD和MD Analysis软件包分析RDF（径向分布函数）和RMSD（均方根偏差）。可惜的是，PDB文件不能承载速度信息，因此我们用c++重新写了一个VASP2GRO程序，输出可以记录原子位置和原子速度的GRO轨迹，它是 GROMACS的私有文件格式，但是也被目前的大部分处理软件支持，比如可视化软件VMD。另外，VASP软件只输出了最后一帧的原子速度，因此无法得到与速度相关的性质，比如速度自相关函数等。我们借鉴樊哲勇老师博客中的方法(http://blog.sciencenet.cn/blog-3102863-1159419.html)，通过向后差分的方法近似得到每一帧的原子速度。原理如下：

这样处理就舍去了第一帧的速度。如果想要得到比较精确的原子速度，可以通过牛顿定律求t时刻的速度vt:

而不同时刻的原子受力，原子位置在OUTCAR中均有输出。本程序未采用该方法。VASP2GRO可以快速从OUTCAR中读取所需要的信息，并自动计算第2帧到最后一帧的原子位置和原子速度，输出到GROMACS的轨迹gro中。与之前的XDATCAR_toolkit.py一样，我们对周期性进行了处理，以保证计算得到的原子速度不会出现异常。

我们提供了编译好的VASP2GRO.exe和VASP2GRO_WIN.exe，分别为Linux和Window版本，可执行程序和其源代码可以在我的Github下载。（https://github.com/tamaswells/VASP_script/tree/master/VASP2GRO）。

程序的使用如下,在linux的终端中输入：

1chmod u+x VASP2GRO.exe

2./VASP2GRO.exe

程序自动会读取OUTCAR的信息，并输出带有原子位置和原子速度的gro轨迹，一个伪的拓扑文件XDATCAR.top和一个伪的输入文件XDATCAR.mdp。它们不能用于进行分子动力学计算，但是对我们使用GROMACS的分析功能已经绰绰有余了。

接下来我们就使用它强大的分析功能帮助我们分析VASP的动力学结果。GROMACS是生物模拟领域常用的分子模拟软件，其拥有运行速度快，后处理功能强的特点。现阶段AIMD的后处理软件尚未完善，我们的软件起到了连接VASP和GROMACS的桥梁作用，借用传统分子模拟领域的优秀分析代码，助力我们处理VASP的动力学结果。

首先需要安装GROMACS，如果你是Ubuntu或者Centos的用户，你可以使用apt-get install gromacs或者yum install gromacs在线安装，你也可以使用参考Sob的并行安装方法安装（http://sobereva.com/457）。安装后可以输入gmx或者gmx_mpi测试是否安装好。

接下来我们使用GROMACS的功能处理我们转化得到的轨迹。先使用trjconv功能将得到的gro文件转成二进制的trr文件。如果你是并行安装的，需要将gmx替换成gmx_mpi。

1gmx trjconv -f XDATCAR.gro -o XDATCAR.trr

再使用预编译引擎将输入文件打包成一个输入tpr文件：

1gmx grompp -f XDATCAR.mdp -c XDATCAR.gro -p XDATCAR.top -o em.tpr

接着我们使用GROMACS神奇的分组功能将H原子和O原子分成一组以便后续处理。

1gmx make_ndx -f XDATCAR.gro

默认的只有3组，包含了所有的原子。我们输入a H就会添加一组由H原子构成的一组，输入a O添加O原子组，再输入q保存退出。生成的index.ndx就包含了每个组包含的原子的原子序号。如果想合并O原子组H原子组，可以输入3 | 4回车就会生成第5组。

1Reading structure file

2Going to read 0 old index file(s)

3Analysing residue names:

4There are: 24 Other residues

5Analysing residues not classified as Protein/DNA/RNA/Water and splitting into groups...

6

7 0 System : 24 atoms

8 1 Other : 24 atoms

9 2 MOL : 24 atoms

10

11 nr : group '!': not 'name' nr name 'splitch' nr Enter: list groups

12'a': atom '&': and 'del' nr 'splitres' nr 'l': list residues

13't': atom type'|': or 'keep' nr 'splitat' nr 'h': help

14'r': residue 'res' nr 'chain' char

15"name": group 'case': case sensitive 'q': save and quit

16'ri': residue index

17

18> a H

19

20Found 16 atoms with name H

21

22 3 H : 16 atoms

23

24> a O

25

26Found 8 atoms with name O

27

28 4 O : 8 atoms

29

30> q

我们尝试做O原子的速度自相关函数。此时需要带上index.ndx以区分不同的原子组

1gmx velacc -f XDATCAR.trr -o vacf.xvg -n index.ndx

输入4来得到O原子的速度自相关函数。

1Command line:

2 gmx velacc -f XDATCAR.trr -o vacf.xvg -n index.ndx

3

4Group 0 ( System) has 24 elements

5Group 1 ( Other) has 24 elements

6Group 2 ( MOL) has 24 elements

7Group 3 ( H) has 16 elements

8Group 4 ( O) has 8 elements

9Select a group: 4

10Selected 4: 'O'

11trr version: GMX_trn_file (single precision)

得到的vacf.xvg是个含有时间，速度自相关函数值的数据文件，可以利用xmgrace作图，也可以手动提取后用Origin Pro作图。这里我们提供了一个脚本xvg.py，使用Python的Matplotlib作图：

1import numpy as np

2from matplotlib import pyplot as plt

3import sys

4import os

5

6#------------------ FONT_setup ----------------------

7font = {'family' : 'Arial',

8'color' : 'black',

9'weight' : 'normal',

10'size' : 16.0,

11 }

12

13

14if len(sys.argv) <2:

15#print(")

16if sys.version[0]=='2':

17 input=raw_input

18 file=input("please with xvg file name-->")

19else:

20 file=sys.argv[1]

21plt.style.use("ggplot")

22

23ifnot os.path.exists(file):

24 print("No file exists")

25 sys.exit(0)

26

27data=[]

28with open(file,'r') as reader:

29for index,line in enumerate(reader):

30if"title"in line:

31 title = eval(' '.join(line.split()[2:]))

32elif"xaxis"in line and"label"in line:

33 xlabel=eval(' '.join(line.split()[3:]))

34elif"yaxis"in line and"label"in line:

35 ylabel=eval(' '.join(line.split()[3:]))

36elif ((not line.startswith("@")) and (not line.startswith("&"))\

37and (not line.startswith("#"))):

38 data.append(list(map(float,line.split())))

39datas=np.array(data)

40plt.plot(datas[:,0],datas[:,1:])

41

42plt.ylabel(ylabel,fontdict=font)

43plt.xlabel(xlabel,fontdict=font)

44plt.xticks(fontsize=font['size']-3)

45plt.yticks(fontsize=font['size']-3)

46plt.title(title,fontdict=font)

47

48plt.show()

GROMACS的强大不止于此，李继存老师的博客上有详细的教程可供学习。(https://jerkwin.github.io/GMX/GMXprg/)。

预览时标签不可点

不喜欢

Scan to Follow

Got It

Scan with Weixin to

use this Mini Program

CancelAllow

CancelAllow

CancelAllow

微信扫一扫可打开此内容，

使用完整服务

: ，，，，，，，，，，，，.VideoMini ProgramLike，轻点两下取消赞Wow，轻点两下取消在看ShareCommentFavorite听过
