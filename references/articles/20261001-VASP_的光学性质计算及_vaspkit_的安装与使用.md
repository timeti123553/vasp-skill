# VASP 的光学性质计算及 vaspkit 的安装与使用

- 来源: `https://zhuanlan.zhihu.com/p/26836978`（**与 `og:url` 核对一致**；页面内 `saved from url=(0037)…` 亦吻合）
- 作者: 知乎 @chempeng，编辑于 2017-05-11（**VASPKIT 0.51 时代**的教程）
- 类型: html（用户另存网页后收录）
- 标签: 知乎, 他人文章, 光学性质, VASPKIT, LOPTICS, 介电函数
- ⚠️ **时代说明**：文中的 VASPKIT 菜单编号（光学在 `51`）与安装流程属于 **0.5x 版本**；**新版 VASPKIT 的菜单与流程已不同**（评论区里就有读者发现新版会显示 `Reading Input Parameters From INCAR File...`）——使用时以本机版本为准。
- 正文字数: 11066

---
使用的软件：VASP, Origin, SshClient, [vaspkit](http://pan.baidu.com/s/1miQCxhY)

# 一 光学性质计算

在完成结构优化和静态计算后，拷贝 scf 文件夹为 optic （结构优化和静态计算参见 [VASP的能带计算与绘图](https://zhuanlan.zhihu.com/p/26389347)）

cp -rf scf optic

编辑 optic 文件夹下 INCAR

## INCAR

SYSTEM=x ISTART=0 ENCUT=350 EDIFF=1E-5 IBRION=-1 # change POTIM=0.25 NSW=0 # change EDIFFG=-1E-2 ISMEAR=0 SIGMA=0.05 PREC=ACCURATE ISIF=2 NPAR=1 # change 4 to 1 #LWAVE=FALSE #LCHARG=FALSE LREAL=Auto #IALGO=48 ISYM=0 NBANDS=x # add LOPTICS=.TRUE. # add

- 注：NBANDS=x x 为 OUTCAT 中 NBANDS*2, 可使用 grep 命令查询

grep NBANDS OUTCAR

提交作业，计算完成后，可查看 OUTCAR 文件，有计算得出介电常数 (Dielectric constant) 的实部和虚部。

frequency dependent IMAGINARY DIELECTRIC FUNCTION (independent particle, no local field effects) E(ev) X Y Z XY YZ ZX

frequency dependent REAL DIELECTRIC FUNCTION (independent particle, no local field effects) E(ev) X Y Z XY YZ ZX

使用 vaspkit 程序对计算结果进行处理。

# 二 vaspkit 的安装与使用

## 安装 Installation

### 使用 SshClient 将已下载的 [vaspkit](http://pan.baidu.com/s/1miQCxhY) 导入 linux 服务器，安装步骤：

tar -zvxf vaspkit.*.tar.gz cd vaspkit.*/src modify the Makefile file based on your machine environment; make

- Note that the formats of POSCAR, CONCAR and CHGCAR files in VASP.5.x are slightly different from those in VASP.4.x. Please set the vasp5=.false. in the src/module.f90 file if you use VASP.4.x

### 设置环境变量

vi ~/.bashrc alias opt="~/software/vaspkit.0.51/examples/optic/optics.sh" alias kit="~/software/vaspkit.0.51/src/vaspkit" source ~/.bashrc

- You need to preparethe [http://REAL.IN](http://REAL.IN) and [http://IMAG.IN](http://IMAG.IN) files which include the real and imaginary parts of frequencydependent complex dielectric function. There is a bash script optics.sh as a reference in the vaspkit.*/examples/optic/ could help you to prepare the [http://real.in](http://real.in) and [http://imag.in](http://imag.in) files.

## 光学数据处理

输入命令opt产生 [http://REAL.IN](http://REAL.IN) 和 [http://IMAG.IN](http://IMAG.IN) 文件，依次输入命令kit和51，屏幕显示如下

+---------------------------------------------------+ | VASPKIT Version: 0.51 (10 Oct. 2016) | | A Postprocessing Toolkit For VASP.5.x Code | | Developed By Vei WANG (wangvei@icloud.com) | +---------------------------------------------------+ =============== Structural Options ================== 2) Elastic Constant Calculator 3) Structure Converting 4) Supercell Building 5) EOS Fitting 6) Symmetry Toolkit 7) K-Mesh Generating 8) Band-Structure Path Generating (experimental) =============== Electronic Options ================== 11) Total DOS 12) Projected DOS 13) l-m Decomposed DOS 21) Band-Structure 22) Projected Band-Structure 23) 3D Band-Structure for Two-Dimensional Materials 24) One Specific Band-Structure ======== Charge Density & Potential Options ========= 31) CHG Density 32) Spin Density 33) Spin-Up & -Down Density 34) CHG Difference 35) Spin Density Difference 41) Planar-Average CHG 42) Planar-Average POT =============== Optical Options ===================== 51) Linear Optics ================ Misc Utilities ===================== 91) Semiconductor Calculator 92) VASP2BoltzTraP 0) Quit ------------>> 51 +---------------------------------------------------+ | Please prepared IMAG.in and REAL.in files | | before runing optics | |...................................................| | Calculate absorb,refractive,energylossspectrum, | | extinctionr and reflectivity (in eV). | +---------------------------------------------------+ -->> (1) Reading IMAG.in and REAL.in Files... -->> (2) Written Optical Files Succesfully! +---------------------------------------------------+ | * DISCLAIMER * | | CANNOT Guarantee Reliability of VASPKIT Code | | CHECK Your Results for Consistency If Necessary | | (^.^) GOOD LUCK (^.^) | +---------------------------------------------------+

输出文件 ABSORB.dat，REFRACTIVE.dat，REFLECTIVITY.dat，EXTINCTION.dat 和 ENERGYLOSSSPECTRUM.dat，依次为 absorption coefficient, refractive coefficient, reflectivity coefficient, extinction coefficient and energy-loss function。导出使用 Origin 作图即可。

附：相关光学性质计算公式

相关参考

1.

[How can we calculate the absorption spectra by vasp? - ResearchGate](https://www.researchgate.net/post/How_can_we_calculate_the_absorption_spectra_by_vasp)

2.

[LOPTICS: frequency dependent dielectric matrix](http://cms.mpi.univie.ac.at/vasp/vasp/LOPTICS_frequency_dependent_dielectric_matrix.html)

3.

[Dielectric properties of SiC](http://cms.mpi.univie.ac.at/wiki/index.php/Dielectric_properties_of_SiC)

原文链接：[VASP 的光学性质计算及 vaspkit 的安装与使用](http://chempeng.coding.me/2017/03/17/VASP%20%E7%9A%84%E5%85%89%E5%AD%A6%E6%80%A7%E8%B4%A8%E8%AE%A1%E7%AE%97%E5%8F%8A%20vaspkit%20%E7%9A%84%E5%AE%89%E8%A3%85%E4%B8%8E%E4%BD%BF%E7%94%A8/)

编辑于 2017-05-11 10:49

计算化学

https://www.zhihu.com/topic/19667110

HR赫莲娜京东自营旗舰店

赫莲娜黑绷带50PX面霜，一夜提松垮 紧塑外轮廓立即购买

的广告

未登录用户

35 条评论

默认

最新

https://www.zhihu.com/people/6de4f64505fbaca53828e3704b255e7d

[荼靡](https://www.zhihu.com/people/6de4f64505fbaca53828e3704b255e7d)

介电常数中xx,yy是代表什么？，如果我要画图，那应该选那一列的数值

2021-01-28

https://www.zhihu.com/people/cc36a3595e0cbae8d00bdece24023688

[薛定谔的猫](https://www.zhihu.com/people/cc36a3595e0cbae8d00bdece24023688)

你好，我想请问一下在计算光学性质时最后运行vaspkit的[http://IMAG.in](http://IMAG.in) 和 [http://REAL.in](http://REAL.in) 文件如果我不通过运行脚本创建，我应该怎么创建这两个文件呢，可以直接将介电函数的实部和虚部复制过来吗？

2021-08-30

https://www.zhihu.com/people/32e09a2431699a638fc8817ee24d4ece

[Zalrahda](https://www.zhihu.com/people/32e09a2431699a638fc8817ee24d4ece)

INCAR中不必要的参数太多

2017-07-08

https://www.zhihu.com/people/6b9967686d187cf7242d911ffc9645c6

[zz11](https://www.zhihu.com/people/6b9967686d187cf7242d911ffc9645c6)

你好，可以麻烦问一下计算介电常数时可以加电场吗？为什么我加电场之后得不到想要的结果

2025-06-02

https://www.zhihu.com/people/a71cc02961072887690d18058cd6b2a8

[知乎用户WEwUOe](https://www.zhihu.com/people/a71cc02961072887690d18058cd6b2a8)

想请问一下，有没有人算出来以后光吸收，是MS计算结果或者文献结果的10倍是怎么回事啊？峰的位置也对不上

2024-01-19

https://www.zhihu.com/people/1311bc2f55ffaf3aa56710a0e7240e37

[tswcbyy](https://www.zhihu.com/people/1311bc2f55ffaf3aa56710a0e7240e37)

老师您好，请问能否设置计算介电常数的频率范围呢？想要算特定波段的介电常数，目前算出频率范围里不包含，且不必要的频率算了很多。

2023-02-15

https://www.zhihu.com/people/a43fdedae9f8dbc65c7779c4feaee2b2

[小姜是我的呀](https://www.zhihu.com/people/a43fdedae9f8dbc65c7779c4feaee2b2)

请问生成的.dat文件中xx yy zz xy yz zx六列怎么做图？看文献中一般都是只有一个曲线。我用(xx+yy+zz)/3得到的光吸收系数都比文献中的要大5、6倍，请问正常吗？

2022-11-06

https://www.zhihu.com/people/4b3974acda46eec1991922e294c56112

[苏也玥](https://www.zhihu.com/people/4b3974acda46eec1991922e294c56112)

为什么有的光学性质计算出来纵坐标单位是%

2021-08-31

https://www.zhihu.com/people/cc36a3595e0cbae8d00bdece24023688

[薛定谔的猫](https://www.zhihu.com/people/cc36a3595e0cbae8d00bdece24023688)

为什么我最后运行 vaspkit 是 -->> (01) Reading Input Parameters From INCAR File...而不是-->> (01) Reading [http://IMAG.in](http://IMAG.in) and [http://REAL.in](http://REAL.in) Files...呢？

2021-08-30

https://www.zhihu.com/people/f295b1a0a1be2d6a8a498ee9a91aaaf8

[水果皮儿](https://www.zhihu.com/people/f295b1a0a1be2d6a8a498ee9a91aaaf8)

请问介电函数dielectric function和静介电常数stastic dielectric constant有什么联系，vasp怎么算后者？

2020-08-29


---

> ✂️ 已裁掉知乎页面尾部 UI（查看全部评论入口、热榜、推荐阅读等）。
> **提炼去向**：整理成 `workflows.md` **第三十六节（光学性质）**：
> ① 流程与 INCAR（**`LOPTICS=.TRUE.`、`NBANDS` ×2、`NPAR` 调小、`ISYM=0`**）；
> ② ⚠️ `OUTCAR` 里那两段介电函数的**前提是「独立粒子 + 无局域场效应」**——这正是「结果与文献差几倍」的首要原因；
> ③ VASPKIT 后处理（老版 `opt` + `51` → 五个 `.dat`）与**新版流程差异**；
> ④ **VASPKIT 安装步骤**（改 `Makefile`、`make`、**VASP 4.x 要设 `vasp5=.false.`**）；
> ⑤ **画图选列的规矩**（对角 vs 非对角分量、各向异性分方向）与**「结果差 5~10 倍」的六条排查清单**；
> ⑥ 评论区两个问题的答案（**静态介电常数用 `LEPSILON`**、**`LOPTICS` 不需要外加电场**）。
> 📌 本库注：原文的 INCAR 是 **vaspkit 生成的模板**（评论里也有人指出「不必要的参数太多」），本库在 §36.1 只保留了**必要项**并标出光学特有项，便于直接抄。
