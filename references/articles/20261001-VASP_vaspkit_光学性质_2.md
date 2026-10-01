# VASP vaspkit 光学性质|2

- 来源: `https://zhuanlan.zhihu.com/p/669635613`（经知乎开放平台 CLI `me content --content-url` 读取，**本人文章**；`Data.Url` 与链接一致）
- 类型: html（zhihu-cli JSON → HTML 后收录；公式已内联 **65 处**）
- 标签: 知乎, 本人文章, 光学性质, VASPKIT, GW, BSE, 二维材料, 石墨烯
- 📌 本系列第 2 篇：第 1 篇（`p/625881446`）讲 `710`/`711` 与实操，本篇讲**理论公式 + GW-BSE 流程**。
- ⚠️ 抓取质量：**三段绘图代码在导出时丢失了空格与换行**（如 `importnumpyasnp`），本库**保留原样**并另在 `scripts/reference/` 存了**重排版本**（见文末「本库注」）。
- 正文字数: 11629

---
注：VASP 计算介电函数时只考虑了带间直接跃迁，因此该方法仅适用于半导体或绝缘体体系，不适用金属体系。

注：Si 和石墨烯的计算参考的 B 站的视频“[vaspkit计算材料光学性质gw+bse【凝聚态计算入门】](https://www.bilibili.com/video/BV1c94y1b7tH/?spm_id_from=333.880.my_history.page.click&vd_source=eb94d534d845c731deff83873982824b)”。

注：相关的 VASP 输入文件可以在 vaspkit/examples 中的 optical_2D 和 Si_BSE_optical 文件中找到。

所需工具：

- VASP（5.4.4）

- vaspkit（1.4.1）

- python（3.11）

注：使用 vaspkit 1.2.4 版本进行数据处理的时候会有些问题，最好使用更新版本的 vaspkit 。

如有错误，欢迎指正。

## 理论

[https://doi.org/10.1016/j.cpc.2021.108033](https://doi.org/10.1016/j.cpc.2021.108033)

理论为上述文章的光学部分。

计算光谱，最主要的是计算出材料的介电函数，只要算出了材料的介电函数 \($$\varepsilon(\omega)$$\) ，其他的光谱的相关数据可以通过介电函数推导出来。

\(\varepsilon(\omega)=\varepsilon_{1}(\omega)+i \varepsilon_{2}(\omega)\)

\($$\varepsilon_{1}(\omega)$$\) 是介电函数的实部；

\($$\varepsilon_{2}(\omega)$$\) 是介电函数的虚部；

\($$\omega$$\) 是光子频率；

在单电子图景中，介电函数的虚部 \($$\varepsilon_{2}(\omega)$$\) 由以下方程式得出：

\(\displaystyle\varepsilon_{2}(\omega)=\frac{4 \pi^{2} e^{2}}{\Omega} \lim _{q \rightarrow 0} \frac{1}{q^{2}} \times \sum_{c, v, \mathbf{k}} 2 w_{\mathbf{k}} \delta\left(E_{c}-E_{v}-\omega\right)|\langle c|\mathbf{e} \cdot \mathbf{q}| v\rangle|^{2}\)

\($$\langle c|\mathbf{e} \cdot \mathbf{q}| v\rangle$$\) 是占据态 \($$(v)$$\) 到空态 \($$(c)$$\) 的光学跃迁；

\($$\bf e$$\) 是光的偏振方向；

\($$\bf q$$\) 是电子的动量算符；

通过在具有相应权重因子 \($$\omega_k$$\) 的特殊 \($$k$$\) 点上求和来执行 \($$k$$\) 上的积分。

介电函数 \($$\varepsilon_{1}(\omega)$$\) 的实部可以由下式给出的 Kramers-Kronig 关系式确定：

\(\displaystyle\varepsilon_{1}(\omega)=1+\frac{2}{\pi} P \int_{0}^{\infty} \frac{\varepsilon_{2}\left(\omega^{\prime}\right) \omega^{\prime}}{\omega^{2}-\omega^{2}+i \eta} d \omega^{\prime}\)

其中 \($$P$$\) 表示主值， \($$\eta$$\) 是复数平移参数。

综上，我们可以得到与频率相关的线性光谱：

折射率： \(\displaystyle n(\omega)=\left(\frac{\sqrt{\varepsilon_{1}^{2}+\varepsilon_{2}^{2}}+\varepsilon_{1}}{2}\right)^{\frac{1}{2}}\)

消光系数： \(\displaystyle k(\omega)=\left(\frac{\sqrt{\varepsilon_{1}^{2}+\varepsilon_{2}^{2}}-\varepsilon_{1}}{2}\right)^{\frac{1}{2}}\)

吸收系数： \(\displaystyle \alpha(\omega)=\frac{\sqrt{2} \omega}{c}\left(\sqrt{\varepsilon_{1}^{2}+\varepsilon_{2}^{2}}-\varepsilon_{1}\right)^{\frac{1}{2}}\)

能量损失函数： \(\displaystyle L(\omega)=\operatorname{Im}\left(\frac{-1}{\varepsilon(\omega)}\right)=\frac{\varepsilon_{2}}{\varepsilon_{1}^{2}+\varepsilon_{2}^{2}}\)

反射率： \(\displaystyle R(\omega)=\frac{(n-1)^{2}+k^{2}}{(n+1)^{2}+k^{2}}\)

其中反射率 \($$R(\omega)$$\) 可以通过介电函数的实部 \($$\varepsilon_{1}(\omega)$$\) 和虚部 \($$\varepsilon_{2}(\omega)$$\) 计算出来。

在下中，我们给出了通过在 \($$\rm G_0W_0$$\) 近似顶部求解 Bethe-Salpeter 方程（BSE）确定的硅的线性光谱。可以发现，吸收系数仅在 \($$\rm 3.0~eV$$\) 之后才变得显著。

这是因为硅具有间接带隙，导致在可见光区域的吸收系数低。由于 GW 近似包括依赖于单粒子格林函数 G 和动态屏蔽库仑相互作用 W 的自能项中的交换和相关效应，因此它可以在多体准粒子框架内校正从 DFT 获得的单电子本征值。

此外，由于在确定 W 时缺乏梯形图而产生的误差可以通过 Bethe-Salpeter 方程（BSE）的求解来概括。

可以预期，GW-BSE 计算的光学性质与实验产生了更好的一致性。在单次 \($$\rm G_0W_0$$\) 近似中，单电子格林函数 G 在一次迭代中自洽更新，而屏蔽库仑相互作用 W 固定在其初始值。

应该指出的是，对于低维材料，折射率、消光系数、吸收系数、能量损失函数和反射率对应的公式并不明确，因为当使用具有足够大的层间距离 \($$L$$\) 的层的周期性堆叠来模拟低维系统以避免标准 DFT 计算中 2D 片状晶体的周期性图像之间的相互作用时，介电函数不是直接的。

为了避免厚度问题，使用光学电导率 \($$\sigma_{2 D}(\omega)$$\) 来表征 2D 片材的光学特性。基于麦克斯韦方程，三维光学电导率可以表示为：

\(\sigma_{3 D}(\omega)=i[1-\varepsilon(\omega)] \varepsilon_{0} \omega\)

其中， \($$\varepsilon(\omega)$$\) 是 \($$\varepsilon(\omega)=\varepsilon_{1}(\omega)+i \varepsilon_{2}(\omega)$$\) 中给出的频率相关复介电函数， \($$\varepsilon_0$$\) 是真空的介电常数， \($$\omega$$\) 是入射波的频率。平面内 2D 光学电导率通过方程与对应的 \($$\sigma_{3 D}(\omega)$$\) 分量直接相关：

\(\sigma_{2 D}(\omega)=L \sigma_{3 D}(\omega)\)

其中 \($$L$$\) 是模拟单元中的层厚度。

当我们假设法向入射时，标准化反射率 \($$R(\omega)$$\) 、透射率 \($$T(\omega)$$\) 和吸光度 \($$A(\omega)$$\) 与独立的 2D 晶体片的光偏振无关：

标准化反射率： \(\displaystyle R=\left|\frac{\tilde{\sigma} / 2}{1+\tilde{\sigma} / 2}\right|^{2}\)

透射率： \(\displaystyle T=\frac{1}{|1+\tilde{\sigma} / 2|^{2}}\)

吸光度： \(\displaystyle A=\frac{\operatorname{Re} \tilde{\sigma}}{|1+\tilde{\sigma} / 2|^{2}}\)

其中 \($$\displaystyle \tilde{\sigma}(\omega)=\frac{\sigma_{2 \mathrm{D}}(\omega)}{\varepsilon_{0} c}$$\) 是归一化的电导率（ \($$c$$\) 是光速）。

由于只考虑带间贡献，标准化反射率 \($$R(\omega)$$\) 、透射率 \($$T(\omega)$$\) 和吸光度 \($$A(\omega)$$\) 所对应的公式对于具有 \($$A+T+R=1$$\) 限制的半导体和绝缘 2D 晶体是有效的。

通常，2D片的反射率非常小，吸光度可以用 \($$\displaystyle \tilde{\sigma}(\omega)$$\) 的实部，即 \($$\displaystyle A(\omega)=\frac{\operatorname{Re} \sigma_{2 D}(\omega)}{\varepsilon_{0} c}$$\) 来近似。

为了证明这一功能，独立石墨烯和磷烯单层的 PBE 计算的线性光谱如下图所示。我们的结果与现有的理论光学曲线非常一致。

（a）石墨烯和（c）磷烯的频率相关光学电导率 \($$\sigma_{2D}(\omega)$$\) 的实部（蓝线）和虚部（红线）[单位为 \($$\displaystyle \sigma_{0}=\frac{e^{2}}{4\hbar}$$\) ]。

（b）石墨烯和（d）亚磷烯的吸收光谱 \($$A(\omega)$$\) 。沿磷烯扶手椅和 Z 字形方向偏振的入射光分别用实线和虚线表示。

垂直颜色线高亮显示可见光区域。

## 硅（Si）

分四步计算：

- 第一步：DFT 计算；

- 第二步：空态计算；

- 第三步： \($$\rm G_0W_0$$\) 近似；

- 第四步：BSE 计算；

### 第一步

需要准备的文件：

- INCAR

- POSCAR

- KPOINTS

- POTCAR

- 作业提交脚本

System = Si PREC = Normal ; ENCUT = 250.0 ISMEAR = 0 ; SIGMA = 0.01 KPAR = 8 EDIFF = 1.E-8

KPAR = 8 ：并行设置，使用的核数必须是该值的整数倍。

### 第二步

需要准备的文件：

- INCAR

- POSCAR

- KPOINTS

- POTCAR

- WAVECAR（第一步计算生成的文件）

- 作业提交脚本

System = Si PREC = Normal ; ENCUT = 250.0 ALGO = EXACT ; NELM = 1 ISMEAR = 0 ; SIGMA = 0.05 NBANDS = 216 LOPTICS = .TRUE. ;

NBANDS = 216 ：设置足够多的能带数，是因为需要计算空轨道。

### 第三步

需要准备的文件：

- INCAR

- POSCAR

- KPOINTS

- POTCAR

- WAVECAR（第二步计算生成的文件）

- WAVEDER（第二步计算生成的文件）

- 作业提交脚本

System = Si PREC = Normal ; ENCUT = 250.0 ALGO = GW0 ISMEAR = 0 ; SIGMA = 0.05 NELM = 1 ; NBANDS = 216 NOMEGA = 72 LWAVE = .TRUE. LSPECTRAL= .TRUE. LOPTICS= .TRUE.

生成的临时文件的数目是和 KPOINTS 中 k 点的数目有关系的。

### 第四步

需要准备的文件：

- INCAR

- POSCAR

- KPOINTS

- POTCAR

- WAVECAR（第三步计算生成的文件）

- WAVEDER（第三步计算生成的文件）

- WAVECAR.chi（第三步计算生成的文件）

- *.tmp（第三步计算生成的所有临时文件）

- 作业提交脚本

System = Si PREC = Normal ENCUT = 250.0 ALGO = BSE ISMEAR = 0 SIGMA = 0.05 NBANDS = 216 NOMEGA = 72 LSPECTRAL= .TRUE. LOPTICS= .TRUE. OMEGAMAX= 10 NBANDSO = 16 NBANDSV = 16 NEDOS=3000

### 计算结果分析

在运行完上面四步后，在第四步的目录下运行 vaspkit ：

vaspkit \($$\Rightarrow$$\) 71 \($$\Rightarrow$$\) 711 \($$\Rightarrow$$\) 1 \($$\Rightarrow$$\) 1

注：vaspkit 1.4.1 版本比之前的版本多了最后一步，即可单独的输出想要的折射率、消光系数、吸收系数、能量损失函数和反射率对应的图。

之后在第四步的目录下运行 Python 脚本：optical.py

之后生成 PDF 文件：Optical.pdf

optical.py 脚本内容：

importnumpyasnpimportmatplotlibasmplmpl.rcParams['font.size']=13.frommatplotlibimportpyplotaspltimportmatplotlib.tickerastickerfig=plt.figure(figsize=(14,5))fig.tight_layout()plt.subplots_adjust(wspace=0.35,hspace=0)ax=fig.add_subplot(141)optical=np.loadtxt("ABSORPTION.dat")ax.plot(optical[:,0],optical[:,1],lw=3,color='blue')plt.xlim(2,6)plt.xticks(np.arange(2,6.1,1))plt.ylim(0,2.5E6)plt.xlabel("Photon energy (eV)")plt.ylabel(r"Absorption coefﬁcient $\alpha(\omega)$ (cm$^{-1}$)")plt.ticklabel_format(style='sci',axis='y',scilimits=(0,0))ax=fig.add_subplot(142)optical=np.loadtxt("REFRACTIVE.dat")ax.plot(optical[:,0],optical[:,1],lw=3,color='blue')plt.xlim(0,8)plt.xticks(np.arange(0,8.1,2))plt.ylim(0,8)plt.yticks(np.arange(0,8.1,2))plt.xlabel("Photon energy (eV)")plt.ylabel(r"Refractive index $n(\omega)$")ax=fig.add_subplot(143)optical=np.loadtxt("REFLECTIVITY.dat")ax.plot(optical[:,0],optical[:,1],lw=3,color='blue')plt.xlim(0,8)plt.xticks(np.arange(0,8.1,2))plt.ylim(0,.8)plt.yticks(np.arange(0,0.81,.2))plt.xlabel("Photon energy (eV)")plt.ylabel(r"Reflectivity $R(\omega)$")ax=fig.add_subplot(144)optical=np.loadtxt("EXTINCTION.dat")ax.plot(optical[:,0],optical[:,1],lw=3,color='blue')plt.xlim(0,8)plt.xticks(np.arange(0,8.1,2))plt.ylim(0,6)plt.yticks(np.arange(0,6.1,1))plt.xlabel("Photon energy (eV)")plt.ylabel(r"Extinction coefficient $k(\omega)$")plt.savefig('Optical.pdf',dpi=100)

Optical.pdf 内容：

与文献的数据进行对比：

计算结果与文献结果符合。

## 石墨烯（graphene）

### INCAR

System = Si PREC = Normal ; ENCUT = 400.0 ISMEAR = 0 ; SIGMA = 0.20 NELM = 30; NBANDS = 216 NOMEGA = 72 LWAVE = .TRUE. LSPECTRAL= .TRUE. LOPTICS= .TRUE. EDIFF = 1E-08 NEDOS = 10001

NBANDS = 216

基态是占据态；激发态是空态；光谱要考虑跃迁。从基态到激发态的跃迁需要足够多的能带才能计算（能带数量要设置足够大的值）。

将下面三个开关都打开：

- LWAVE = .TRUE.

- LSPECTRAL= .TRUE.

- LOPTICS= .TRUE.

注：计算光谱的时候，KPOINTS 中 k 点需要取的非常密。

需要准备的文件：

- INCAR

- POSCAR

- KPOINTS

- POTCAR

- 作业提交脚本

### 计算结构分析

提交完作业后运行 vaspkit ：

vaspkit \($$\Rightarrow$$\) 71 \($$\Rightarrow$$\) 710 \($$\Rightarrow$$\) 1

注：选择 710 是因为石墨烯是二维材料。

石墨烯的光吸收谱：

注：上图纵轴没有单位是百分比 % 。

读取 IMAG_OPTICAL_CONDUCTIVITY_2D.dat 和 REAL_OPTICAL_CONDUCTIVITY_2D.dat 中石墨烯的光学电导率的虚部和实部并画图：

与文献结果进行对比：

我们发现与文献的结果符合。

### 结果处理代码

画石墨烯光吸收谱图的代码：

importmatplotlib.pyplotaspltimportnumpyasnpdefread_transmission_data(file_path):data=[]withopen(file_path,'r')asfile:forlineinfile:ifnotline.strip().startswith('#'):# Skip comment linesparts=line.split()iflen(parts)==3:# Convert each part to float and append to the data listenergy,xx,yy=map(float,parts)data.append((energy,xx,yy))returnnp.array(data)# Converting the list to a numpy arraydefplot_data(data,x_min=None,x_max=None,y_min=None,y_max=None):# Splitting data into energy, xx, and yyenergy,xx,yy=data[:,0],data[:,1],data[:,2]plt.figure(figsize=(7,7))# Plotting xx(%)plt.plot(energy,xx,label='xx(%)',color='blue')# Plotting yy(%)plt.plot(energy,yy,label='yy(%)',color='red')plt.xlabel('Photon energy(eV)')plt.ylabel('Absorption (%)')plt.title('Energy-Absorption_2D')plt.legend()plt.grid(True)# Set the x-axis range if specifiedifx_minisnotNoneorx_maxisnotNone:plt.xlim(x_min,x_max)# Set the y-axis range if specifiedify_minisnotNoneory_maxisnotNone:plt.ylim(y_min,y_max)# Save the figureplt.savefig('Absorption_2D.png',dpi=300)# Save as PNG with high dpi for better qualityplt.show()# Replace with the path to your filefile_path='ABSORPTION_2D.dat'x_min=0# Set the minimum x-axis value (modify as needed)x_max=15# Set the maximum x-axis value (modify as needed)y_min=0# Set the minimum y-axis value (modify as needed)y_max=24# Set the maximum y-axis value (modify as needed)data=read_transmission_data(file_path)plot_data(data,x_min,x_max,y_min,y_max)

画石墨烯光学电导率的虚部和实部图的代码：

importreimportmatplotlib.pyplotaspltdefsplit_data(row):# Use regular expressions to find matches for the patternpattern=r"([+-]?[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)"matches=re.findall(pattern,row)returnmatchesdefread_and_split_data(file_path):# Reading the filewithopen(file_path,'r')asfile:lines=file.readlines()# Splitting each row of the datasplit_rows=[split_data(row)forrowinlines[1:]]# Assuming the first line is headerreturnsplit_rowsdefplot_data(data1,data2,x_range=None,y_range=None,save_path=None):# Convert data to numeric values and transposedata1_numeric=[[float(value)forvalueinrow]forrowindata1]data1_transposed=list(zip(*data1_numeric))data2_numeric=[[float(value)forvalueinrow]forrowindata2]data2_transposed=list(zip(*data2_numeric))# Extracting columnsenergy1,xx1,yy1=data1_transposedenergy2,xx2,yy2=data2_transposed# Plottingplt.figure(figsize=(7,7))plt.plot(energy1,xx1,label='XX (REAL)',color='red',linewidth=2)plt.plot(energy1,yy1,label='YY (REAL)',linestyle='dashed',linewidth=2)plt.plot(energy2,xx2,label='XX (IMAG)',color='black',linewidth=2)plt.plot(energy2,yy2,label='YY (IMAG)',linestyle='dashed',linewidth=2)plt.xlabel('Photon energy (eV)',fontsize=14,fontweight='bold')plt.ylabel('Optical conductivity $\sigma_{2D}/\sigma_{0}$',fontsize=14,fontweight='bold')plt.title('Graphene',fontsize=16,fontweight='bold')plt.legend(fontsize=12)# Setting axis ranges if specifiedifx_rangeisnotNone:plt.xlim(x_range)ify_rangeisnotNone:plt.ylim(y_range)# Save the plot to a file if save path is providedifsave_pathisnotNone:plt.savefig(save_path)plt.show()# File pathsfile_path1='REAL_OPTICAL_CONDUCTIVITY_2D.dat'file_path2='IMAG_OPTICAL_CONDUCTIVITY_2D.dat'# Read and split data from both filesdata1=read_and_split_data(file_path1)data2=read_and_split_data(file_path2)# Plot the data with specified x and y axis ranges and save the plotplot_data(data1,data2,x_range=(0,15),y_range=(-5,10),save_path='plot.png')

---

## 本库注（收录时补充，非原文内容）

1. ⚠️⚠️ **适用范围这条一定要记住**：**VASP 的介电函数只含带间直接跃迁 ⇒ 只适用于半导体/绝缘体，不适用金属**（金属的主导贡献是带内/Drude）。本库已把它提到 `workflows.md` §36.10 开头，并写进 `errors.md` §七。
2. ⭐⭐ **五个导出量的完整公式**（`n`、`k`、`α`、`L`、`R`）此前库里只有「有这些文件」而没有公式——本篇补齐，并指出**只有 `ε₁`/`ε₂` 是原始输出、其余都能自己算**（`§36.10 ②`）。
3. ⭐⭐ **二维材料的正确物理量是光学电导率 `σ_2D = L·σ_3D`**：原文从原理上说明**介电函数对低维体系不是 well-defined 的**（厚度 `L` 的取法影响数值），并给出 `A + T + R = 1` 与近似式 `A ≈ Re σ_2D/(ε₀c)`——**这从理论上解释了 §36.8 的「NOT suitable for low-dimensional materials」与 §36.9 的 `710`**。
4. ⭐ **方法层级**：DFT(`LOPTICS`) → **GW** → **GW-BSE**；以 Si（间接带隙，吸收要到 ~3.0 eV 才显著）为例说明为什么 GW-BSE 与实验更一致 ⇒ **PBE 光学适合定性，发表级要往上走**（`§36.10 ④`）。
5. ⭐ **GW-BSE 四步实操**已整理成 `§36.11` 的表格（含 `WAVEDER`/`WAVECAR.chi`/`*.tmp` 的传递链，以及 `ALGO=EXACT/GW0/BSE`、`NOMEGA`、`OMEGAMAX`、`NBANDSO`/`NBANDSV`）——**注意 `WAVEDER` 缺了就做不了第三步**。
6. ⭐ **石墨烯的 `710` 流程回答了一个旧疑问**：`ABSORPTION_2D.dat` **纵轴单位是 `%`**（库内另一篇教程的评论区问过「为什么有的光学性质纵坐标是 %」）；它的列结构是「能量 + `xx` + `yy`」三列，与 3D 的七列不同。
7. ⚠️ **工具版本**：原文提醒 **VASPKIT 1.2.4 做这步「会有一些问题」，建议用更新版本**（本篇用 1.4.1，其数据处理的最后一步比旧版多一个选择）。
8. 📌 **脚本收录说明**：三段绘图代码原文**粘连不可直接运行**，本库在 `scripts/reference/` 存了**重排版本**（`optical_plot_pdf.py`、`graphene_absorption_plot.py`、`graphene_optical_conductivity_plot.py`），每个文件头部都注明**「本库重排、未运行验证、原文形态保留在来源文章里」**。
