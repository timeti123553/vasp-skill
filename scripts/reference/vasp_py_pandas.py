#===============================================================================
# 参考脚本（原样收集 · 未验证 · 未运行）
# 来源文章: articles/20261001-VASP_Python_数据挖掘_1.md
# 原文链接: https://zhuanlan.zhihu.com/p/591424842
# 用途    : 从 OUTCAR 用正则提取任意量（示例 LOOP+: cpu time）→ pandas 画图 + 存 CSV
# 依赖    : Python + pandas + re
# 功能说明: workflows.md 第二十节（pandas 路线）（本目录只放源码文本，说明以那里为准）
# 抓取质量: 原网页代码块**丢失换行与缩进** —— 下面正文是原样保存的文本，
#           只能读逻辑，不能直接执行。
#===============================================================================

#!/public/home/XXX/miniconda3/bin/python3.9importpandasaspdimportref=open('OUTCAR')t=f.read()match=re.findall(r"(LOOP\D: cpu time) (\d{2}\.\d{4})",t)df=pd.DataFrame(data=match)df1=df[1].astype(float)a=df1.plot(x="step",y="time")fig=a.get_figure()fig.savefig('1.png')df.columns=['name','LOOP+:cpu time']df.to_csv("1.csv")
