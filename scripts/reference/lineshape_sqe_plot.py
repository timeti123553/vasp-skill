# =============================================================================
# 参考脚本（从文章收集）
# 来源文章: 20261001-TDEP计算高温声子谱_天帝君豪的个人博客.md
# 原文链接: https://tiandijunhao.github.io/2020/06/28/tdep-ji-suan-sheng-zi-pu/
# 用途    : 读 TDEP 的 outfile.sqe.hdf5 画声子线型/动态结构因子 S(q,E) 热图
# 依赖    : numpy, matplotlib, h5py
# 抓取质量: ⚠️ 原文代码块导出时**丢失了空格与换行**；本文件是**本库重排**版本，
#           只补空白、未改动逻辑，**未运行验证**；原文形态保留在来源文章的 md 里。
# =============================================================================

import matplotlib.pyplot as plt
import numpy as np
import h5py as h5
from matplotlib.colors import LogNorm

# open the sqe file
f = h5.File('outfile.sqe.hdf5', 'r')

# get axes and intensity
x = np.array(f.get('q_values'))
y = np.array(f.get('energy_values'))
gz = np.array(f.get('intensity'))

# add a little bit so that the logscale does not go nuts
gz = gz + 1E-2

# for plotting, turn the axes into 2d arrays
gx, gy = np.meshgrid(x, y)

# x-ticks
xt = np.array(f.get('q_ticks'))
# labels for the x-ticks
xl = f.attrs.get('q_tick_labels').split()

# label for y-axis
plt.pcolormesh(gx, gy, gz, norm=LogNorm(vmin=gz.min(), vmax=gz.max()), cmap='afmhot')

# set the limits of the plot to the limits of the data
plt.axis([x.min(), x.max(), y.min(), y.max()])
plt.xticks(xt, xl)
plt.tight_layout()
plt.show()
