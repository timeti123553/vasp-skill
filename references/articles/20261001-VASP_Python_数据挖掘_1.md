# VASP+Python 数据挖掘|1

- 来源: `https://zhuanlan.zhihu.com/p/591424842`
- 类型: html
- 标签: 知乎, 本人文章, OUTCAR, 数据提取, pandas
- ⚠️ 抓取说明：本文代码块来自网页高亮组件，**空格/缩进在抓取时丢失**（如 `import pandas as pd` 变成 `importpandasaspd`），**不要直接复制运行**，按逻辑重写。
- 正文字数: 1627

---
本篇文章使用的环境是：centos 下的 miniconda 的 jupyter lab 。

脚本中需要用到 python 包：re 和 pandas 。

本篇文章要提取 OUTCAR 中的信息是：

注：这是通过在命令行输入：grep LOOP+ OUTCAR 提取的结果。

注：这篇文章的任务是将信息通过 python 脚本提取出来，并画图保存为 csv 表格数据。

## 写脚本的原因

在使用 VASP 完成计算后，尽管有各种各样的后处理程序来处理我们的计算结果，但是这些处理结果的程序并不能处理所有的输出数据。

在 OUTCAR 或者其他的输出文件中，有很多信息需要我们自己写脚本提取，所以我就写了这篇文章来和大家交流。

## 基本思路

- 通过 python 包 re 来实现通过正则表达式来提取输出文件中的信息。

- 通过 python 包 pandas 将提取到的信息画图和保存。

注：对于初学者，正则表达式可能比较写。我们可以通过一些在先的测试网站来测试我们写的正则表达式，比如：

[regex101: build, test, and debug regex](https://regex101.com/)

## 1 提取数据

导入我们需要的 python 包：

importpandasaspdimportre

从当前目录下读取数据：

f=open('OUTCAR')t=f.read()match=re.findall(r"(LOOP\D: cpu time) (\d{2}\.\d{4})",t)foriinrange(100):print(match[i])

输出结果为：

## 2 画图制表

将数据转化成 pandas 所需要的形式：

df=pd.DataFrame(data=match)df

输出结果为：

将我们需要画图的那一列数据转化为浮点型（否则无法画图）：

df1=df[1].astype(float)

将浮点型的数据画图：

a=df1.plot(x="step",y="time")fig=a.get_figure()fig.savefig('1.png')

输出的结果为：

注：这里我加上了 x 轴和 y 轴的坐标名称，但是画出的图没有（不知道有没有人知道原因）。

给每一列加上列名：

df.columns=['name','LOOP+:cpu time']df

输出结果为：

将得到的数据保存为 csv 格式：

df.to_csv("1.csv")

在当前目录下，我们可以得到我们画的图和制的表：

我们制的表可以直接在 jupyter lab 上查看：

## 3 脚本

#!/public/home/XXX/miniconda3/bin/python3.9importpandasaspdimportref=open('OUTCAR')t=f.read()match=re.findall(r"(LOOP\D: cpu time) (\d{2}\.\d{4})",t)df=pd.DataFrame(data=match)df1=df[1].astype(float)a=df1.plot(x="step",y="time")fig=a.get_figure()fig.savefig('1.png')df.columns=['name','LOOP+:cpu time']df.to_csv("1.csv")

注：第一行是系统中你的 python 所在的位置。

将上述脚本保存为 vasp-py 文件。

在存在 OUTCAR 的当前目录下，运行代码（赋予改文件执行权限）：

chmod +x vasp-py

在当前目录下输入命令：

./vasp-py

然后该目录下就会输出我们所需要的表格和图片。

如有错误，欢迎指正。
