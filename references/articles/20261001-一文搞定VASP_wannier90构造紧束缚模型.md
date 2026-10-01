# 一文搞定VASP+wannier90构造紧束缚模型

- 来源: `https://zhuanlan.zhihu.com/p/355317202`（与原始 HTML 的 `og:url` 核对一致）
- 作者: 知乎 @蓝蓝的天坑（“老王”）；原文最初来自“材料基因论坛”Brook 斑竹的帖子，编辑于 2021-06-21
- 类型: html（用户另存网页后收录；zhida 搜索链接已在收录时压平）
- 标签: 知乎, 他人文章, Wannier90, 紧束缚模型, MLWF, SOC, 拓扑
- 正文字数: 15407

---
今天老王来介绍一下VASP与wannier90结合构建基于第一性原理的紧束缚模型。

首先登录wannier90官网下载wannier90 2.1版本

[Download - Wannier90www.wannier.org/download/](http://www.wannier.org/download/)

为什么是2.1版本呢？

因为2.1版本是可以与VASP结合的最新版本。但是2.1版本默认安装与VASP接口并不好，主要是借助肖承诚博士写了一个Fortran的接口（[https://github.com/Chengcheng-Xiao/VASP2WAN90_v2_fix](https://github.com/Chengcheng-Xiao/VASP2WAN90_v2_fix)）（这里感谢肖博士），需要注意的是这个接口是针对VASP 5.4.4版本的。1.2版本与VASP的接口是好的，所以1.2版本默认安装就好。表1对比了两个版本的不同，1.2版本的主要缺点就在于不能构建向上自旋和向下自旋的能带，也就是没有自旋轨道耦合作用的铁磁和反铁磁体系。（至少老王没有想到好办法可以实现）

1. 安装

1.1 wannier90 2.1安装

首先，解压安装包

tar -zxvf wannier90-2.1.0.tar.gz

其次，进入文件夹

cd wannier90-2.1.0/

然后，准备编译文件（这里老王用的是ifort，注意要检查ifort和mpiifort执行命令）

cp config/make.inc.ifort make.inc

接着，编译

make

完成后，编译库，得到libwannier.a文件

make lib

1.2 VASP编译（注意以上接口VASP2WAN90_v2_fix只针对VASP 5.4.4）

首先拷贝VASP2WAN90_v2_fix接口文件中的mlwf.patch 到VASP代码编译目录下。然后执行如下命令。

patch -p0 < mlwf.patch

接着在VASP makefile.include 文件中加入下面两行。注意路径。

CPP_OPTIONS+=-DVASP2WANNIER90v2 LLIBS+=/path/to/your/wannier90_distro/libwannier.a

最后编译即可

make all

2. 构建wannier紧束缚模型

构建wannier紧束缚模型的过程包括三步：

第一步，常规的自洽计算

第二步，能带分析，得到费米面附近的主要轨道

第三步，Wannierization

2.1 nosoc 体系

以MoSi2N4单层为例。（参考Chemical vapor deposition of layered two-dimensional MoSi2N4 materials一文）

图1. MoSi2N4单层的晶体结构。

图2. MoSi2N4的能带结构。

2.1.1 自洽计算

以下为自洽计算INCAR文件。

Global Parameters ISTART = 1 (Read existing wavefunction; if there) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 500 (Cut-off energy for plane wave basis set, in eV) PREC = High (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) Static Calculation ISMEAR = 0 (gaussian smearing method) SIGMA = 0.05 (please check the width of the smearing) NELM = 60 (Max electronic SCF steps) EDIFF = 1E-08 (SCF energy convergence; in eV)

2.1.2 能带分析

拷贝自洽计算的CHGCAR文件到能带计算目录下，加入参数ICHARG = 11， LORBIT = 11， 即可计算能带并且得到PROCAR文件，PROCAR文件可以用于fatband分析。

能带计算INCAR如下：

Global Parameters ISTART = 1 (Read existing wavefunction; if there) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 500 (Cut-off energy for plane wave basis set, in eV) PREC = High (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) Static Calculation ISMEAR = 0 (gaussian smearing method) SIGMA = 0.05 (please check the width of the smearing) NELM = 60 (Max electronic SCF steps) EDIFF = 1E-08 (SCF energy convergence; in eV) ICHARG = 11 LORBIT = 11

图3，MoSi2N4的fatband图。

从图3看费米面附近的能带成分主要是Mo原子的d轨道和N原子的p轨道。

2.1.3 Wannierization

通过上面图3，我们发现费米面附近主要是Mo原子的d轨道和Si，N原子的p轨道。后面解释为什么加了Si的p轨道。因此我们设置投影部分为，

begin projections Mo : d Si : p N : p end projections

wannier90.win 文件是用于构造wannier函数的初始输入文件。

在这个文件最开始只要设置num_bands, num_wann，frozen窗口 以及投影轨道部分就好。老王习惯把这些都写上。

wannier90.win 文件设置为：

num_bands = 48 #num_bands = NBANDS of INCAR >= num_wann num_wann = 23 # number of wannier bands dis_win_min = -20.00d0 dis_win_max = 30d0 dis_froz_min = -11.50d0 # energy window dis_froz_max = 4.0d0 #dis_num_iter = 1000 num_iter = 200 num_print_cycles = 20 #spinors = .true. # projections begin projections Mo : d Si : p N : p end projections #Bandstructure plot #restart = plot bands_plot = true #fermi_energy = 7.9099 #fermi_surface_plot = true begin kpoint_path K -0.3333 0.6666 0.0 G 0.0 0.0 0.0 G 0.0 0.0 0.0 M 0.0 0.5 0.0 M 0.0 0.5 0.0 K -0.3333 0.6666 0.0 end kpoint_path bands_num_points 101 bands_plot_format gnuplot xmgrace

这里关键是num_wann的设置，num_wann <= num_bands, 而num_bands与INCAR中NBANDS是一样的。

num_wann大小和投影轨道数和投影原子数有关。

计算细节如下：

s轨道1个电子记1，p轨道3个电子记3，d轨道5个电子记5。

num_wann = 1 x 5 + 2 x 3 + 4 x 3 = 23

其中1，2，4为原胞中Mo，Si，N的数量，3，5为p和d轨道的电子数。

begin projections Mo : d Si : p N : p end projections

VASP中除INCAR外，KPOINTS，POTCAR，POSCAR均与自洽计算一致。

INCAR在自洽计算的基础上添加LWANNIER90 参数，更多wannier投影参数控制可以参考肖承诚博士VASP2WAN90_v2_fix接口的GitHub。

https://github.com/Chengcheng-Xiao/VASP2WAN90_v2_fix/wiki/Keywords

具体INCAR设置如下：

Global Parameters ISTART = 1 (Read existing wavefunction; if there) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 500 (Cut-off energy for plane wave basis set, in eV) PREC = High (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) Static Calculation ISMEAR = 0 (gaussian smearing method) SIGMA = 0.05 (please check the width of the smearing) NELM = 60 (Max electronic SCF steps) EDIFF = 1E-08 (SCF energy convergence; in eV) LWANNIER90 = TRUE

注意，INCAR中使用NPAR参数会出错。

运行完VASP以后这个文件会自动补全。包括结构信息，k点信息。

然后检查是否生成wannier90.amm，wannier90.mmn 以及wannier90.eig文件。

有了这三个文件就可以进一步调节参数，构造wannier函数了。

运行命令为：

wannier90.x wannier90 &

这里后面一个winner90代表wannier90.win的文件.win前面的部分。如果你的win文件是name.win运行的地方就可以是

wannier90.x name &

运行过程中当num_bands > num_wann 有个迭代过程，控制迭代步数可以通过

dis_num_iter = 200 # 迭代1，默认200步 num_iter = 200 # 迭代2，默认200步

最后会生成wannier90.chk文件，restart计算会读取这个文件。

加入能带部分的话第一次运行就会出来，wannier90_band.dat文件，这个可以用来和DFT结果对比。

#Bandstructure plot #restart = plot bands_plot = true #fermi_energy = 7.9099 #fermi_surface_plot = true begin kpoint_path K -0.3333 0.6666 0.0 G 0.0 0.0 0.0 G 0.0 0.0 0.0 M 0.0 0.5 0.0 M 0.0 0.5 0.0 K -0.3333 0.6666 0.0 end kpoint_path bands_num_points 101 bands_plot_format gnuplot xmgrace

计算结果如下：

图4. 不同轨道投影的结果。

由于，Si的p轨道在M点价带位置有贡献，而不考虑Si 的p轨道会导致这个位置拟合的不好。所以我们选择了Si的p轨道。

2.1.4 影响投影质量的关键参数

=> num_bands

总能带数num_bands，要有足够多的DFT能带数，以至于足够覆盖所需要研究的能带以及覆盖投影子具有投影成分的能带。

=> 投影轨道选择

选择投影轨道之前，请彻底做一次能带成分分析，也就是画Fatband图和PDOS图。确认费米面附件的轨道成分，把这些轨道作为投影轨道。

begin projections Mo : d Si : p N : p end projections

=>能量窗口

包括解纠缠窗口和Frozen窗口。这两个能量窗口是相对于没有进行费米能修正之前的能带的。Frozen窗口里尽量包含整数条能带，尽量不包含其他未投影的轨道。dis_froz_min的设置有时候也可以设置小点，这样可以包括更多的能带，以至于收敛更快。

dis_win_min = -20.00d0 dis_win_max = 30d0 dis_froz_min = -11.50d0 # energy window dis_froz_max = 4.0d0

=> k-mesh密度

增加k-mesh 密度。尤其是在拓扑半金属中k空间中较小区域发生能带反转的是时候。增加kmesh的意义在于可以得到更远距离的hopping，对于金属体系比较重要。

tips：

建议一开始设置num_iter=0，看看你构造的Wannier函数的spread怎么样。如果spread太大，那就调节这些参数，使得这个spread减小。如果你实在没辙了，那就使用num_iter吧

2.1.4 判断投影质量的方法

在投影过程中判断。主要是wannier90.wout中的WF centre 和spreads。WF centre在原子位置附近。spread大小于晶格常数相当，越小越好。

括号中是 wannier函数的中心，最后一列是 Spread。对比笛卡尔坐标我们可以看出Mo,Si,N原子依次排布。

另外，如图4，可以通过对比DFT的能带和Wannier函数插值后的能带。看看会不会相等，如果你看到了一些曲折的条纹，那么说明你的Wannier函数不够局域。

2.2 soc 体系 (包括 soc， soc + 铁磁， soc + 反铁磁)

同样以MoSi2N4单层为例。

2.2.1 自洽计算

自洽计算在nosoc基础上添加 LSORBIT = TRUE， 改用vasp_ncl 脚本提交。

2.2.2 能带分析

能带分析与nosoc相同。一般能带成分不会发生改变，所以投影轨道也不需要发生改变。

2.2.3 Wannierization

这里注意，首先需要打开 spinors = .true. ，

其次，修改num_wann到nosoc的两倍。这里是46， nosoc是23。

顺便调整num_bands 到大于num_wann 的值，注意要等于NBANDS。

num_bands = 96 #num_bands = NBANDS of INCAR >= num_wann num_wann = 46 # number of wannier bands dis_win_min = -20.00d0 dis_win_max = 30d0 dis_froz_min = -11.50d0 # energy window dis_froz_max = 4.0d0 #dis_num_iter = 1000 num_iter = 200 num_print_cycles = 20 spinors = .true. # projections begin projections Mo : d Si : p N : p end projections #Bandstructure plot #restart = plot bands_plot = true #fermi_energy = 7.9099 #fermi_surface_plot = true begin kpoint_path K -0.3333 0.6666 0.0 G 0.0 0.0 0.0 G 0.0 0.0 0.0 M 0.0 0.5 0.0 M 0.0 0.5 0.0 K -0.3333 0.6666 0.0 end kpoint_path bands_num_points 101 bands_plot_format gnuplot xmgrace

结果如下：

图5. MoSi2N4自旋轨道耦合能带图。

2.3 nosoc + 铁磁 （包括 nosoc + 铁磁 和 nosoc + 反铁磁）

以MnBi2Te4单层为例。

前两个步骤是一样的。我们直接来说第三步，wannierization。

在这里我们需要准备两个文件分别对应自旋向上的设置和自旋向下的设置。wannier90.up.win 和 wannier90.dn.win

INCAR中在之前nosoc基础上添加 ISPIN = 2。

Global Parameters ISTART = 1 (Read existing wavefunction; if there) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 500 (Cut-off energy for plane wave basis set, in eV) PREC = High (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) Static Calculation ISMEAR = 0 (gaussian smearing method) SIGMA = 0.05 (please check the width of the smearing) NELM = 60 (Max electronic SCF steps) EDIFF = 1E-08 (SCF energy convergence; in eV) ISPIN = 2 LWANNIER90 = TRU

能带分析发现，Mn的d轨道，Bi和Te的p轨道对费米面附近影响都比较大。所以我们给出如下投影轨道。

[wannier90.up.win](http://wannier90.up.win/)

num_bands = 96 begin projections Mn : d Bi : p Te : p end projections

[wannier90.dn.win](http://wannier90.dn.win/)

num_bands = 96 begin projections Mn : d Bi : p Te : p end projections

在反铁磁体系中两个不同自旋的原子可以用分数坐标来指定。假设MnBi2Te4是AB堆垛。则

wannier90.up.win 中，

begin projections f= 0 0 0 : d Bi : p Te : p end projections

wannier90.dn.win 中，

begin projections f= 0 0 0.5 : d Bi : p Te : p end projections

结果如下：

图6， MnBi2Te4 单层能带自旋向上

图7， MnBi2Te4 单层能带自旋向下

希望大家多多练习，以上理解如有不妥，请指出。

练习案例：

拓扑绝缘体Bi2Se3练习教程，

参考资料：(以下两篇里有很多注意点，请大家参考学习)

[1] Wannier90输入文件中num_wann, num_bands, 和energy window等参数设置规则

[Wannier90输入文件中num_wann, num_bands, 和energy window等参数设置规则](http://blog.sciencenet.cn/blog-2909108-1154273.html)

[2]构造Wannier90函数的要点

[[转载]构造Wannier90函数的要点](https://www.jianshu.com/p/ed0c5fd0d14f)

---以上内容最初来自“材料基因论坛”的Brook斑竹，因为没有找到原帖，故而找了这个转载版本。

如需转载请后台联系，谢谢。


---

> ✂️ 已裁掉知乎页面自带的 UI（**68 条评论** / 广告位 / 话题链接 / 推荐阅读）。
> 评论里有一条作者的实用回答已提炼进 `workflows.md` §25.7：**自旋极化体系必须分别运行**`wannier90.x wannier90.up` 与 `wannier90.x wannier90.dn`。
> ⚠️ 记录一处原文笔误：接口输出的文件应为 **`wannier90.amn`**（原文写作 “`.amm`”）；流程说明里已按标准文件名书写。
