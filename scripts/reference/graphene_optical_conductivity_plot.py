# =============================================================================
# 参考脚本（从文章收集）
# 来源文章: 20261001-VASP_vaspkit_光学性质_2.md
# 原文链接: https://zhuanlan.zhihu.com/p/669635613
# 用途    : 读 REAL_/IMAG_OPTICAL_CONDUCTIVITY_2D.dat 画二维材料光学电导率（纵轴 sigma_2D/sigma_0）
# 依赖    : matplotlib
# 抓取质量: ⚠️ 原文代码块在导出时**丢失了空格与换行**（如 `importnumpyasnp`）。
#           本文件是**本库按可读形式重排**的版本：只补空白、未改动标识符与逻辑；
#           **未运行验证**。原文的原始（粘连）形态保留在来源文章的 md 文件里。
# =============================================================================

import re
import matplotlib.pyplot as plt


def split_data(row):
    # Use regular expressions to find matches for the pattern
    pattern = r"([+-]?[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)"
    matches = re.findall(pattern, row)
    return matches


def read_and_split_data(file_path):
    with open(file_path, 'r') as file:               # Reading the file
        lines = file.readlines()
    split_rows = [split_data(row) for row in lines[1:]]   # first line is header
    return split_rows


def plot_data(data1, data2, x_range=None, y_range=None, save_path=None):
    data1_numeric = [[float(value) for value in row] for row in data1]
    data1_transposed = list(zip(*data1_numeric))
    data2_numeric = [[float(value) for value in row] for row in data2]
    data2_transposed = list(zip(*data2_numeric))

    energy1, xx1, yy1 = data1_transposed             # Extracting columns
    energy2, xx2, yy2 = data2_transposed

    plt.figure(figsize=(7, 7))
    plt.plot(energy1, xx1, label='XX (REAL)', color='red', linewidth=2)
    plt.plot(energy1, yy1, label='YY (REAL)', linestyle='dashed', linewidth=2)
    plt.plot(energy2, xx2, label='XX (IMAG)', color='black', linewidth=2)
    plt.plot(energy2, yy2, label='YY (IMAG)', linestyle='dashed', linewidth=2)
    plt.xlabel('Photon energy (eV)', fontsize=14, fontweight='bold')
    plt.ylabel(r'Optical conductivity $\sigma_{2D}/\sigma_{0}$', fontsize=14, fontweight='bold')
    plt.title('Graphene', fontsize=16, fontweight='bold')
    plt.legend(fontsize=12)
    if x_range is not None:                          # Set axis ranges if specified
        plt.xlim(x_range)
    if y_range is not None:
        plt.ylim(y_range)
    if save_path is not None:                        # Save the plot to a file
        plt.savefig(save_path)
    plt.show()


file_path1 = 'REAL_OPTICAL_CONDUCTIVITY_2D.dat'
file_path2 = 'IMAG_OPTICAL_CONDUCTIVITY_2D.dat'
data1 = read_and_split_data(file_path1)
data2 = read_and_split_data(file_path2)
plot_data(data1, data2, x_range=(0, 15), y_range=(-5, 10), save_path='plot.png')
