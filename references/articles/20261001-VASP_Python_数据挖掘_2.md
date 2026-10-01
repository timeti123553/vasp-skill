# VASP+Python 数据挖掘|2

- 来源: `https://zhuanlan.zhihu.com/p/592138877`
- 类型: html
- 标签: 知乎, 本人文章, OUTCAR, 数据提取, numpy, matplotlib
- ⚠️ 抓取说明：本文代码块来自网页高亮组件，**空格/缩进在抓取时丢失**（如 `import numpy as np` 变成 `importnumpyasnp`），**不要直接复制运行**，按逻辑重写。
- 正文字数: 1632

---
本篇文章使用的环境是：centos 下的 miniconda 的 jupyter lab 。

脚本中需要用到 python 包：re 、numpy 和 matplotlib 。

本篇文章要提取 OUTCAR 中的信息是：

注：这是通过在命令行输入：grep LOOP+ OUTCAR 提取的结果。

注：这篇文章的任务是将信息通过 python 脚本提取出来，并画图保存为 csv 表格数据。

## 基本思路

- 通过 python 包 re 来实现通过正则表达式来提取输出文件中的信息。

- 通过 python 包 numpy 和 matplotlib 将提取到的信息画图和保存。

注：对于初学者，正则表达式可能比较难写。我们可以通过一些在先的测试网站来测试我们写的正则表达式，比如：

[regex101: build, test, and debug regex](https://regex101.com/)

## 1 提取数据

导入我们需要的 python 包：

importmatplotlib.pyplotaspltimportnumpyasnpimportre

从当前目录下读取数据：

f=open('OUTCAR')t=f.read()match=re.findall(r"(LOOP\D: cpu time) (\d{2}\.\d{4})",t)foriinrange(100):print(match[i])

输出结果为：

## 2 画图制表

将 list 格式的数据转化为 numpy 格式：

y=[]fornuminmatch:y.append(float(num))

根据提取数据的大小算出步数并制作 x 轴的数据：

a=len(match)x=np.linspace(1,a,a)

画图并将图片保存：

plt.plot(x,y)plt.xlabel('step')plt.ylabel('cpu time (s)')plt.savefig('1.png')plt.show()

输出的结果为：

加上列名，并保存为 csv 格式：

np.savetxt("1.csv",y,delimiter=",",header='cpu time (s)',fmt='%s')

我们制的表可以直接在 jupyter lab 上查看：

## 3 脚本

在 vasp 的输出目录中，我们当然不能一行一行的运行这些代码。我们可以把上面这些代码写成一个 linux 系统中的脚本直接运行。

脚本内容如下：

#!/public/home/XXX/miniconda3/bin/python3.9importmatplotlib.pyplotaspltimportnumpyasnpimportref=open('./OUTCAR')t=f.read()match=re.findall(r"(?<=cpu time )\d{2}\.\d{4}",t)a=len(match)x=np.linspace(1,a,a)y=[]fornuminmatch:y.append(float(num))plt.plot(x,y)plt.xlabel('step')plt.ylabel('cpu time (s)')plt.savefig('1.png')np.savetxt("1.csv",y,delimiter=",",header='cpu time (s)',fmt='%s')

注：第一行是系统中你的 python 所在的位置。

将上述脚本保存为 vasp-py 文件。

在存在 OUTCAR 的当前目录下，运行代码（赋予改文件执行权限）：

chmod +x vasp-py

在当前目录下输入命令：

./vasp-py

然后该目录下就会输出我们所需要的表格和图片。

如有错误，欢迎指正。
