# VASP官网关于IBRION参数的说明

- 来源: `https://www.jun997.xyz/2022/07/20/4b7c346573e6.html`
- 作者: June976（jun997.xyz）；**本文是 VASP Wiki `IBRION` 页的翻译**（<https://www.vasp.at/wiki/index.php/IBRION>）并夹有作者注释
- 类型: html (url)
- 抓取时间: 2026-10-01 12:55:02
- 标签: 博客
- 正文字数: 13112

---
IBRION 参数是 VASP 计算中一个使用频率较高的参数，其功能涉及到离子弛豫、分子动力学和声子计算，同时 [VASP Wiki](https://www.vasp.at/wiki/index.php/The_VASP_Manual)上关于参数的使用给出了非常详细的说明，这里打算把官网的说明简单翻译一下，同时在适当地方可能加入一点注释，主要是为了加深自己的理解，这是原文地址：[https://www.vasp.at/wiki/index.php/IBRION](https://www.vasp.at/wiki/index.php/IBRION)。

# IBRION

可选的设置值：IBRION = -1 | 0 | 1 | 2 | 3 | 5 | 6 | 7 | 8 | 44

默认值：

- 对于 NSW = -1 或者 0, IBRION = -1

其它，IBRION = -1

- 描述： IBRION 参数决定了离子如何更新和移动

对于 IBRION=0, 执行的是分子动力学模拟，所有其它算法的目标都是弛豫到局部最低能量。对于复杂的弛豫问题建议使用共轭梯度算法(IBRION=2)，这一方法拥有最可靠的备份路径。当初始的结构猜测非常糟糕时，阻尼分子动力学(IBRION=3)会很有用。对于接近局部最低能量的情况，RMM-DIIS(IBRION=1)通常是最好的选择。IBRION=5 和 IBRION=6 使用有限差分方法来计算二阶导数(厄米矩阵和声子频率)，而 IBRION=7 和 IBRION=8 使用密度泛函微扰理论来计算这些导数。

# IBRION=-1:不更新离子坐标

离子不移动，但是 [NSW](https://www.vasp.at/wiki/index.php/NSW) 指定的外循环仍然会执行。在每个外循环中，电子的自由度被反复优化(除了测试的目的，这实际上不会起什么作用)。如果不需要更新离子位置，请使用 NSW=0。

# IBRION=0:分子动力学

标准的从头算分子动力学，使用 Verlet 算法(如果VASP与stepprecor.o文件链接，则使用四阶预测校正器)来积分求解牛顿运动方程，[POTIM](https://www.vasp.at/wiki/index.php/POTIM) 参数指定以飞秒为单位的时间步长，[SMASS] 参数可以提供一些额外的控制参数。

## 1.关于 Verlet 算法

Verlet 方法是一种用于积分求解牛顿运动方程(或者更高阶)的数值方法，它经常被用于分子动力学模拟中粒子运动轨迹的求解，对于牛顿运动方程，形式为：

dvdt=a(t),dxdt=v(t)\frac{dv}{dt}=a(t),\frac{dx}{dt}=v(t) dtdv​=a(t),dtdx​=v(t)

其中a(t)=a(x(t),v(t),t)a(t)=a(x(t),v(t),t)a(t)=a(x(t),v(t),t)，我们知道，a(t)a(t)a(t)、v(t)v(t)v(t)和x(t)x(t)x(t)都是关于t的连续函数，如果我们要实现数值求解，就必须离散化，因此可以把时间t划分成等长的时间间隔，来逐步求解，这样通过将vn+1v_{n+1}vn+1​和xn+1x_{n+1}xn+1​作泰勒展开即可得到：

vn+1=vn+anΔt+O[(Δt2)]xn+1=xn+vnΔt+12an(Δt)2+O[(Δt)3]v_{n+1}=v_n + a_n\Delta t+O[(\Delta t^2)] \\ x_{n+1}=x_n + v_n\Delta t + \frac{1}{2}a_n(\Delta t)^2 + O[(\Delta t)^3] vn+1​=vn​+an​Δt+O[(Δt2)]xn+1​=xn​+vn​Δt+21​an​(Δt)2+O[(Δt)3]

对于 Verlet 算法，递推关系为：

xn+1=2xn−xn−1+anΔt2an=a(xn)x_{n+1} = 2x_n - x_{n-1} + a_n\Delta t^2 \\ a_n = a(x_n) xn+1​=2xn​−xn−1​+an​Δt2an​=a(xn​)

可以看到，上式中并不包含速度项，另一种包含速度的是 Velocity-Verlet 算法，这一方法方法中包含速度项，迭代公式为：

xn+1=xn+vnΔt+12anΔt2vn+1=vn+an+an+12Δtx_{n+1} = x_n + v_n\Delta t + \frac{1}{2}a_n\Delta t^2 \\ v_{n+1} = v_n + \frac{a_n + a_{n+1}}{2}\Delta t xn+1​=xn​+vn​Δt+21​an​Δt2vn+1​=vn​+2an​+an+1​​Δt

以上迭代公式中加入了速度项，使用更为广泛。

参考资料：

- [https://en.wikipedia.org/wiki/Verlet_integration](https://en.wikipedia.org/wiki/Verlet_integration)

- [https://www.physics.udel.edu/~bnikolic/teaching/phys660/numerical_ode/node5.html](https://www.physics.udel.edu/~bnikolic/teaching/phys660/numerical_ode/node5.html)

## 2.关于VASP分子动力学计算的一些提示

这部分内容同样来自vaspwiki的官网：[https://www.vasp.at/wiki/index.php/Molecular_dynamics_calculations](https://www.vasp.at/wiki/index.php/Molecular_dynamics_calculations)。

为了运行基本的分子动力学计算，需要执行以下步骤：

- 选择一个足够大的超胞

- 如果继续计算，则将 CONTCAR 复制到 POSCAR 或者在 POSCAR 文件中提供原子的初始速度，如果初始没有提供原子的速度，那么原子的初始速度将是随机的，这是完全可以的，但是用户必须知道由于初始速度是完全随机的，不同计算中原子的轨迹将很难进行对比

INCAR 文件中主要需要设置的参数：

- IBRION=0:执行分子动力学计算

- POTIM:分子动力学运行的时间步长

- NSW:分子动力学运行的步数

- TEBEG/TEEND:设置热浴的初始/结束温度

- ISIF:决定系综的类型

- MDALGO:决定了使用那种热浴，常规的分子动力学由一位数字决定，但是在有偏分子动力学中，对于vasp6和更高版本，同样是一位数字，但是在vasp5.X版本中用两位数字决定，第一位数字决定热浴类型，第二位决定分子动力学类型。

- 可选的系综和热浴类型：

[热浴](https://www.vasp.at/wiki/index.php/Category:Thermostats)

[系综](https://www.vasp.at/wiki/index.php/Category:Ensembles)[Andersen](https://www.vasp.at/wiki/index.php/Andersen_thermostat)[Nose-Hoover](https://www.vasp.at/wiki/index.php/Nose-Hoover_thermostat)[Langevin](https://www.vasp.at/wiki/index.php/Langevin_thermostat)[Multiple Andersen](https://www.vasp.at/wiki/index.php/MDALGO#MDALGO.3D13:_Multiple_Anderson_thermostats)

[NVE](https://www.vasp.at/wiki/index.php/NVE_ensemble)[MDALGO](https://www.vasp.at/wiki/index.php/MDALGO)=1, [ANDERSEN_PROB](https://www.vasp.at/wiki/index.php/ANDERSEN_PROB)=0.0

[NVT](https://www.vasp.at/wiki/index.php/NVT_ensemble)[MDALGO](https://www.vasp.at/wiki/index.php/MDALGO)=1[MDALGO](https://www.vasp.at/wiki/index.php/MDALGO)=2[MDALGO](https://www.vasp.at/wiki/index.php/MDALGO)=3[MDALGO](https://www.vasp.at/wiki/index.php/MDALGO)=13

[ISIF](https://www.vasp.at/wiki/index.php/ISIF)=2[ISIF](https://www.vasp.at/wiki/index.php/ISIF)=2[ISIF](https://www.vasp.at/wiki/index.php/ISIF)=2[ISIF](https://www.vasp.at/wiki/index.php/ISIF)=2

[NpT](https://www.vasp.at/wiki/index.php/NpT_ensemble)not availablenot available[MDALGO](https://www.vasp.at/wiki/index.php/MDALGO)=3not available

[ISIF](https://www.vasp.at/wiki/index.php/ISIF)=3

[NpH](https://www.vasp.at/wiki/index.php/NpH_ensemble)[MDALGO](https://www.vasp.at/wiki/index.php/MDALGO)=3, [ISIF](https://www.vasp.at/wiki/index.php/ISIF)=3, [LANGEVIN_GAMMA_L](https://www.vasp.at/wiki/index.php/LANGEVIN_GAMMA_L)=0.0

# IBRION=1:离子弛豫(RMM-DIIS)

对于 IBRION=1，准牛顿算法被用来将离子弛豫到基态，力和应力张量被用来确定寻找平衡位置的搜索方向(不考虑总能量)，这一算法在初始位置接近局部最小值时非常快和高效，但是如果初始猜测位置不好，则会失败(在这种情况下使用 IBRION=2)。由于该算法建立了Hessian矩阵的近似值，因此需要非常精确的力否则将无法收敛，一个有效的解决办法是把 NELMIN 参数的值设为4或8(对于简单体相材料4就足够，而对于电荷密度收敛非常缓慢的复杂表面，可能需要设置为8)。这样会强制在每个离子步之间最少有4到8个电子步，并保证力在每一(离子)步中都收敛。

实现的算法被称作 RMM-DIIS 。它通过考虑来自先前迭代的信息隐式计算逆 Hessian 矩阵的近似值，刚开始时 Hessian 矩阵是对角的并且对角元等于 POTIM 。如果需要，来自旧步骤的信息(可能导致线性依赖)会自动从迭代历史记录中删除。保存在迭代历史中的向量数量对应于 Hessian 矩阵的秩不得超过的自由度，显然自由度的它的自由度是3*(NIONS-1)，但是对称性和约束可以降低这一自由度。

有两种内置算法可以从迭代历史中删除信息：

- 如果在INCAR中指定了 [NFREE](https://www.vasp.at/wiki/index.php/NFREE) 参数，在迭代历史中仅保留了 NFREE 个离子步的迭代历史(近似 Hessian 矩阵的秩不超过 NFREE)。

- 如果没有指定 NFREE 参数，是否从迭代历史中删除信息的标准是基于逆 Hessian 矩阵的特征值谱：如果逆 Hessian 矩阵的一个特征值大于8，则丢弃来自先前步骤的信息。

对于复杂问题，NFREE 通常可以设置为一个很大的值(10-20)，但是低维系统需要小心地设置(或则最好是精确计算自由度的数量)。NFREE增加到超过20几乎不能提高收敛性，如果 NFREE 设得太大，RMM-DIIS算法可能会发散。

一个合理的 POTIM 参数非常重要，并且对于计算的加速效果显著。我们建议使用 IBRION=2 或者运行一些测试计算来找到一个合适的 POTIM 参数。

# IBRION=2:离子弛豫(共轭梯度算法)

共轭梯度算法用来将离子弛豫到它们的基态上，在第一步离子(以及晶胞形状)沿着最陡的方向变化(如计算出的力或应力矩阵的方向)。共轭梯度算法需要一个线性优化器，它分为几个步骤执行：

- 首先让离子向着搜索方向行进一个试验步，该步的长度由 POTIM 参数控制，然后重新计算能量和力。

- 考虑到总能量和力的变化(3条信息)，通过三次(或者二次)插值计算总能量的近似最小值，然后执行一个到近似最低能量结构的修正步。

- 执行修正步后，再重新计算能量和受力，并检查此时离子受力中是否还包含很多沿着搜索方向的成分，如果是，使用 Brent 算法的变体来进一步改进线优化器中的校正步。

总的来说：在第一个离子步中，根据从 POSCAR 中读入的初始结构计算力，第二步时试验步(或预测步)，第三步是修正步。如果在这一步中线性最小化已经足够精确，那么就会开始下一个试验步。

NSTEP:

- 初始位置

- 试验步

- 修正步，即对应于预期最小值的位置

- 试验步

- 校正步

- …

# IBRION=3:离子弛豫(阻尼分子动力学)

如果在 INCAR 文件中通过 SMASS 标签指定了阻尼因子，那么阻尼二阶运动方程将用于更新离子的各个自由度：

x⃗¨=−2αF⃗−μx⃗˙\ddot{\vec{x}} = -2\alpha \vec{F}-\mu \dot{\vec{x}} x¨=−2αF−μx˙

其中 SMASS 指定阻尼因子μ，POTIM 控制 α。使用简单的 velocity verlet 算法来积分这个方程，离散的形式为：

v⃗N+1/2=((1−μ/2)v⃗N−1/2−2αF⃗N)/(1+μ/2)x⃗N+1=x⃗N+v⃗N+1/2\vec{v}_{N+1/2}=((1-\mu /2)\vec{v}_{N-1/2}-2\alpha \vec{F}_N)/(1+\mu /2) \\ \vec{x}_{N+1}=\vec{x}_N + \vec{v}_{N+1/2} vN+1/2​=((1−μ/2)vN−1/2​−2αFN​)/(1+μ/2)xN+1​=xN​+vN+1/2​

可以立即想到，当μ=2时上式等价于一种简单的最速下降法(当然没有线性优化器)。因此，μ=2对应于最大阻尼，而μ=0对应于没有阻尼。最佳阻尼因子取决于 Hessian 矩阵(能量关于原子位置的二阶导数矩阵)。μ的一个合理的猜测通常是0.4。

请注意，我们实现的算法对用户特别友好，因为更改μ通常不需要重新调整时间步长 POTIM。要选择最佳的时间步长和阻尼因子，我们建议采用以下两步程序：首先应该固定μ(例如为1)并调整 POTIM。POTIM 应选择尽可能大，而不会使总能量发散。然后减小μ并保持 POTIM 固定，如果 POTIM 和 SMASS 选择正确，阻尼分子动力学模式通常比共轭梯度法好两倍。

如果 INCAR 文件中没有指定 SMASS 参数，那么会使用 velocity quench 算法。在这种情况下，离子的位置根据以下算法更新：F 是目前的受力，并且α等于 POTIM。这一方程表明，如果力的方向和速度的方向是反平行，速度将被将为0。否则速度将被调整为平行于当前的受力，并且其增量与力成正比。

注意：对于 IBRION=3,需要通过 POTIM 参数来指定一个合理时间步，太大的时间步将导致不收敛，太小的时间步将降低收敛的速度，一个稳定的时间步通常是共轭梯度算法中线性优化步骤中的最小时间步。

# IBRION=5和6：二阶导数， Hessian 矩阵和声子频率(有限差分)

可以在这里找到如何从有限差分中计算声子：[有限差分声子](https://www.vasp.at/wiki/index.php/Phonons_from_finite_differences)。

IBRION=5 在 VASP4.5 版本及以上可用，IBRION=6 从 VASP5.1 版本开始。这两个参数都允许计算 Hessian 矩阵(能量对原子位置的二阶导数)和系统的振动频率。只有区域中心(Γ\GammaΓ点)的频率会自动计算并在之后打印：

1

Eigenvectors and eigenvalues of the dynamical matrix

为了计算 Hessian 矩阵，需要使用有限差分，即每个离子在每个笛卡尔坐标的方向上位移，并根据力计算 Hessian 矩阵。这两种模式在考虑对称性的方式上有所不同。对于 IBRION=5, 所有的原子都在所有的三个笛卡尔坐标方向上位移，即使对于中等大小的高对称系统，也会导致非常大的计算量。对于 IBRION=6,仅考虑对称性上不等价的位移，并使用对称性来填充 Hessian 矩阵的剩余部分。

Selective dynamics目前仅支持 IBRION=5 的情况。在这一情况下，仅仅计算那些在 POSCAR 文件中 Selective dynamic 标签设置为 .TRUE. 部分对应的 Hessian 矩阵的分量。例如：

1

2

3

4

5

6

7

8

9

10

Cubic BN

3.57

0.0 0.5 0.5

0.5 0.0 0.5

0.5 0.5 0.0

1 1

selective

Direct

0.00 0.00 0.00 F F F

0.25 0.25 0.25 T F F

原子2仅在x方向上位移，仅计算 Hessian 矩阵的第二个原子的x分量。

三个参数影响 Hessian 矩阵的计算：[NFREE](https://www.vasp.at/wiki/index.php/NFREE) 参数决定了对于每个离子每个方向的计算选取多少个位移量，而 POTIM 指定位移的步长。如果在输入文件中设定的值太大，位移步长默认被设置为0.015A(从VASP5.1开始)。专业知识表明，这是一个合理的折衷方案。

NFREE=2 使用中心差分，即每个离子被施加一个小的正位移和负位移，±\pm±POTIM，沿着每个笛卡尔方向。对于 NFREE=4，沿着每个笛卡尔坐标的方向施加四个位移量：±\pm±POTIM 和 ±2×\pm2\times±2×POTIM。

对于 NFREE=1，只施加一个位移量(非常不建议使用NFREE=1)。

最后，IBRION=6 和 ISIF ≥\geq≥ 3允许计算弹性常数。弹性张量是通过对晶格进行六次有限变形并从应变——应力关系导出弹性常数来确定的。弹性张量的计算既适用于固定的离子，也适用于弛豫的离子，离子固定时计算的弹性模量信息在这一行之后：

1

SYMMETRIZED ELASTIC MODULI (kBar)

离子的贡献通过转置离子 Hessian 矩阵乘以内部应变张量来计算，相应的贡献写在以下行之后：

1

ELASTIC MODULI CONTR FROM IONIC RELAXATION (kBar)

最终的弹性模量包含离子固定时扭曲的贡献和离子弛豫的贡献，在最后可以总结为：

1

TOTAL ELASTIC MODULI (kBar)

这种方法有一些注意事项，最值得注意的是平面波的截断能能需要足够大以使应力张量收敛，这通常只有在截断能增加到默认值的30%左右才能实现，但强烈建议系统地测试一下，逐步增加截断能(以15%的步长)，直到完全收敛。

通过额外指定 LEPSILON=.TRUE.(线性相应理论)或 LCALCEPS=.TRUE.(有限外场)参数可以计算波恩有效电荷、压电常数和离子对介电张量的贡献。

关于老版本(VASP.5.1之前)的注释：在一些老版本中，INCAR 文件中 NSW 必须设置为1，因为 NSW=0 会不管 INCAR 中 IBRION 的设置值而直接将其设置为-1。

此外，尽管 VASP.4.6 支持 IBRION=5-6，VASP.4.6 不会自动改变k点集合(通常，结构施加位移之后需要使用不同的k点网格)。因此在 VASP.4.6 程序中有限差分方法可能会产生不正确的结果。

## 1.关于 Hessian 矩阵

在数学上，Hessian 矩阵是标量函数或标量场的二阶偏导数的方阵。在 DFT 中，Hessian 矩阵是能量对体系几何结构的二阶导数，在力的计算中应用非常重要，计算过程中使用的位移是笛卡尔位移，因此 Hessian 是基于笛卡尔坐标而不是分数坐标。

Hessian 矩阵的元素定义为：

Hij=δ2EδxiδxjH_{ij} = \frac{\delta ^2E}{\delta x_i \delta x_j} Hij​=δxi​δxj​δ2E​

对于原子数量为N的体系，i的取值有3N个，通过对称性可以进一步减少自由度，详细的计算方法可以参考下面列出的参考文章2。

参考文章：

- [https://en.wikipedia.org/wiki/Hessian_matrix](https://en.wikipedia.org/wiki/Hessian_matrix)

- [http://openmopac.net/manual/Hessian_Matrix.html](http://openmopac.net/manual/Hessian_Matrix.html)

# IBRION=7和8：二阶导数，Hessian 矩阵和声子频率(微扰理论)

从 VASP.5.1 版本开始 IBRION=7 和 IBRION=8 都支持，它会用密度泛函微扰理论计算 Hessian 矩阵，IBRION=7 不会使用对称性，而 IBRION=8 会使用对称性来降低位移的数量，输出结果与 IBRION=5 和6类似。具体来说，有关于离子位移(原子间力常数)的二阶导数以及应变和离子位移(内部应变张量)的混合二阶导数。尽管计算了离子弛豫对弹性张量的贡献，但未确定钳制离子(离子固定)对弹性张量的贡献。如果在 INCAR 文件中指定了 LEPSILON=.TRUE.，波恩有效电荷、压电常数以及离子对介电张量的贡献都会计算。

总的来说，VASP 实现的 DFPT 计算有一点初级，只支持与超胞对称性相同的位移，即使 q=0 的声子。换句话说，VASP 只能计算超胞在Γ点的声子频率，因此，与上面讨论的有限差分方法相比，这部分的代码几乎没有优势，特别是，线性相应仅限于 LDA 和 GGA 泛函，它不能确定弹性张量，因为还没有实现相对于应变张量的线性响应，线性响应方法的唯一优点是它们无需选择有限位移的大小，因此，首先使用线性响应计算声子频率然后切换到有限差分方法来确定最大位移，这样将会产生与线性响应精度相当的结果。

这里需要知道一些技术细节。VASP 通过求解 Sternheimer 方程以确定轨道的线性响应。因此，不需要空轨道。在内部，VASP 的线性响应程序依赖于两个地方的有限差分：

- 第一个地方是计算交换关联泛函的二阶导数：由于大多数泛函并不支持二阶导数的代数求解，VASP 总是通过有限差分来确定每个原子位移后的交换相关势的二阶变化和 PAW 的中心项。

- 第二个地方，在 VASP 确定了轨道的一阶变化之后，它会用有限差分方法来计算所有的二阶导数。

为此，VASP 在选定的方向上将位移施加到选定的原子上，将线性响应计算添加到轨道，最后确定正位移和负位移对力和应力张量作用的差异，可以证明，这分别准确地产生了二阶力常数和内部应变张量。此外，通过在“极化矢量”Eq上收缩轨道地线性响应来“解析地”确定波恩有效电荷。这些计算的结果应该与之前在计算相对于外部场的线性响应时确定的波恩有效电荷非常吻合(有两种不同的方法来计算混合导数)。OUTCAR 文件末尾的最终汇总输出写入了根据外部场的线性响应确定的波恩有效电荷。

# IBRION=44：改进的二聚体方法

参考这里：[https://www.vasp.at/wiki/index.php/Improved_Dimer_Method](https://www.vasp.at/wiki/index.php/Improved_Dimer_Method)

# 一些常识

对于 IBRION=1、2和3，ISIF 标签决定晶胞的形状和离子的位置是否改变，在分子动力学模拟中(IBRION=0)只有在动力学模组使用 Tomas Bucko 时晶胞形状才被允许改变。

所有的弛豫算法都需要在 INCAR 文件中指定 POTIM 的值。对于 IBRION>0，在调用最小化程序之前，力在内部进行缩放，因此对于弛豫，POTIM 并没有物理意义并且只是一个缩放因子，对于很多系统，最佳的 POTIM 在0.5左右，由于准牛顿算法和阻尼算法对这个参数的选择较为敏感，因此如果你不确定最佳的 POTIM 参数应该设多大，使用 IBRION=2 。

在这种情况下，OUTCAR 文件和标准输出设备中将包含一行显示可靠的 POTIM 。对于 IBRION=2，在每个校正步骤之后，以下行将被写入标准输出设备中：

1

2

trial: gam= .00000 g(F)= .152E+01 g(S)= .000E+00 ort = .000E+00

(trialstep = .82)

其中变量 gam 是上一步的共轭参数，g(F) 和 g(S) 分别是力和应力张量的模长，变量 ort 是一个指示器，表明当前的搜索方向与上一个搜索方向正交(对于最佳步长，该值应该远小于 g(F)+g(S) )。变量 trialstep 是当前试验步的步长。该值是使得上一个离子步中实现线最小化的平均步长，通过将当前 POTIM 参数与试验步长相乘，可以确定最佳的 POTIM 。

在每个试验步结束之后，以下信息将被写入到标准输出设备：

1

2

3

trial-energy change: -1.153185 1.order -1.133 -1.527 -.739

step: 1.7275(harm= 2.0557) dis= .12277

next Energy= -1341.57 (dE= -.142E+01)

变量 trial-energy change 是试验步中能量的改变量，1.order 之后的第一个值是根据力计算得出的预期能量变化：(F(start)+F(trial))/2×change of positions.第二和第三个值对应于F(start)×change of positions, and F(trial)×change of positions。

第二行中的第一个值是导致沿当前搜索方向的线最小化的步长。它是使用开始和试验步(力和能量变化)中的数据通过三阶插值公式计算得到的，harm 是使用二阶(或谐波)插值得到的最佳步长，在谐波插值中只使用了力的信息，当接近最小值时，两个值应该相似。dis 是离子在分数坐标中移动的最大距离。next Energy 指示下一个能量应该多大(线最小化优化时的能量)，dE是估算的能量改变值。

在每个试验步结束时，OUTCAR 文件包含以下行：

1

2

3

4

5

6

trial-energy change: -1.148928 1.order -1.126 -1.518 -.735

(g-gl).g = .152E+01 g.g = .152E+01 gl.gl = .000E+00

g(Force) = .152E+01 g(Stress)= .000E+00 ortho = .000E+00

gamma = .00000

opt step = 1.72745 (harmonic = 2.05575) max dist = .12277085

next E = -1341.577507 (d E = 1.42496)

trial-energy change 行前面已经提过. g(Force) 代表 g(F), g(Stress) 代表 g(S), ortho 代表 ort, gamma 代表 gam.第二行中 gamma 之后的值(step: …)之前也讨论过。


---

> ✂️ 已裁掉站点 UI 尾部（归档/标签/订阅/CC 声明等）。
> 正文是**官方 Wiki 的翻译**，可信度高：已把其中可操作的部分收进 `references/incar.md` §三附（选择指南、DFPT `7`/`8` 的局限、**`POTIM` 的最佳值实测法**），并把 **`IBRION=44` 二聚体法**补进 `workflows.md` §二十四（找鞍点，不必先有反应路径）、把 **MD 初始速度随机/积分器**的说明补进 §二十六。
> ⚠️ 抓取说明：文中的数学公式是 LaTeX 渲染，抽取后呈 `\frac{dv}{dt}` 这类源码并与正文粘连，**独立公式块不完整**；需要 Verlet 推导原文请看链接。
