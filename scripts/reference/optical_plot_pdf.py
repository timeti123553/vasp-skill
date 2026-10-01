# =============================================================================
# 参考脚本（从文章收集）
# 来源文章: 20261001-VASP_vaspkit_光学性质_2.md
# 原文链接: https://zhuanlan.zhihu.com/p/669635613
# 用途    : 把 VASPKIT 输出的 ABSORPTION.dat / REFRACTIVE.dat / REFLECTIVITY.dat / EXTINCTION.dat 画成四联图 PDF（Si 的 GW-BSE 例子）
# 依赖    : numpy, matplotlib
# 抓取质量: ⚠️ 原文代码块在导出时**丢失了空格与换行**（如 `importnumpyasnp`）。
#           本文件是**本库按可读形式重排**的版本：只补空白、未改动标识符与逻辑；
#           **未运行验证**。原文的原始（粘连）形态保留在来源文章的 md 文件里。
# =============================================================================

import numpy as np
import matplotlib as mpl

mpl.rcParams['font.size'] = 13.
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker

fig = plt.figure(figsize=(14, 5))
fig.tight_layout()
plt.subplots_adjust(wspace=0.35, hspace=0)

ax = fig.add_subplot(141)
optical = np.loadtxt("ABSORPTION.dat")
ax.plot(optical[:, 0], optical[:, 1], lw=3, color='blue')
plt.xlim(2, 6)
plt.xticks(np.arange(2, 6.1, 1))
plt.ylim(0, 2.5E6)
plt.xlabel("Photon energy (eV)")
plt.ylabel(r"Absorption coefficient $\alpha(\omega)$ (cm$^{-1}$)")
plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

ax = fig.add_subplot(142)
optical = np.loadtxt("REFRACTIVE.dat")
ax.plot(optical[:, 0], optical[:, 1], lw=3, color='blue')
plt.xlim(0, 8)
plt.xticks(np.arange(0, 8.1, 2))
plt.ylim(0, 8)
plt.yticks(np.arange(0, 8.1, 2))
plt.xlabel("Photon energy (eV)")
plt.ylabel(r"Refractive index $n(\omega)$")

ax = fig.add_subplot(143)
optical = np.loadtxt("REFLECTIVITY.dat")
ax.plot(optical[:, 0], optical[:, 1], lw=3, color='blue')
plt.xlim(0, 8)
plt.xticks(np.arange(0, 8.1, 2))
plt.ylim(0, .8)
plt.yticks(np.arange(0, 0.81, .2))
plt.xlabel("Photon energy (eV)")
plt.ylabel(r"Reflectivity $R(\omega)$")

ax = fig.add_subplot(144)
optical = np.loadtxt("EXTINCTION.dat")
ax.plot(optical[:, 0], optical[:, 1], lw=3, color='blue')
plt.xlim(0, 8)
plt.xticks(np.arange(0, 8.1, 2))
plt.ylim(0, 6)
plt.yticks(np.arange(0, 6.1, 1))
plt.xlabel("Photon energy (eV)")
plt.ylabel(r"Extinction coefficient $k(\omega)$")

plt.savefig('Optical.pdf', dpi=100)
