# =============================================================================
# 参考脚本（从文章收集）
# 来源文章: 20261001-VASP_vaspkit_光学性质_2.md
# 原文链接: https://zhuanlan.zhihu.com/p/669635613
# 用途    : 读 ABSORPTION_2D.dat（能量 + xx + yy 三列）画二维材料的光吸收谱（纵轴 %）
# 依赖    : numpy, matplotlib
# 抓取质量: ⚠️ 原文代码块在导出时**丢失了空格与换行**（如 `importnumpyasnp`）。
#           本文件是**本库按可读形式重排**的版本：只补空白、未改动标识符与逻辑；
#           **未运行验证**。原文的原始（粘连）形态保留在来源文章的 md 文件里。
# =============================================================================

import matplotlib.pyplot as plt
import numpy as np


def read_transmission_data(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            if not line.strip().startswith('#'):      # Skip comment lines
                parts = line.split()
                if len(parts) == 3:                   # Convert each part to float and append
                    energy, xx, yy = map(float, parts)
                    data.append((energy, xx, yy))
    return np.array(data)                             # Converting the list to a numpy array


def plot_data(data, x_min=None, x_max=None, y_min=None, y_max=None):
    energy, xx, yy = data[:, 0], data[:, 1], data[:, 2]
    plt.figure(figsize=(7, 7))
    plt.plot(energy, xx, label='xx(%)', color='blue')       # Plotting xx(%)
    plt.plot(energy, yy, label='yy(%)', color='red')        # Plotting yy(%)
    plt.xlabel('Photon energy(eV)')
    plt.ylabel('Absorption (%)')
    plt.title('Energy-Absorption_2D')
    plt.legend()
    plt.grid(True)
    if x_min is not None or x_max is not None:        # Set the x-axis range if specified
        plt.xlim(x_min, x_max)
    if y_min is not None or y_max is not None:        # Set the y-axis range if specified
        plt.ylim(y_min, y_max)
    plt.savefig('Absorption_2D.png', dpi=300)         # PNG, high dpi
    plt.show()


file_path = 'ABSORPTION_2D.dat'      # Replace with the path to your file
x_min = 0                             # modify as needed
x_max = 15
y_min = 0
y_max = 24
data = read_transmission_data(file_path)
plot_data(data, x_min, x_max, y_min, y_max)
