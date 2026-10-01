#===============================================================================
# 参考脚本（原样收集 · 未验证 · 未运行）
# 来源文章: articles/20261001-VASP_Python_数据挖掘_2.md
# 原文链接: https://zhuanlan.zhihu.com/p/592138877
# 用途    : 同一任务的 numpy+matplotlib 版本：后行断言取数 → 画图 → np.savetxt 存 CSV
# 依赖    : Python + numpy + matplotlib + re
# 功能说明: workflows.md 第二十节（numpy+matplotlib 路线）（本目录只放源码文本，说明以那里为准）
# 抓取质量: 原网页代码块**丢失换行与缩进** —— 下面正文是原样保存的文本，
#           只能读逻辑，不能直接执行。
#===============================================================================

#!/public/home/XXX/miniconda3/bin/python3.9importmatplotlib.pyplotaspltimportnumpyasnpimportref=open('./OUTCAR')t=f.read()match=re.findall(r"(?<=cpu time )\d{2}\.\d{4}",t)a=len(match)x=np.linspace(1,a,a)y=[]fornuminmatch:y.append(float(num))plt.plot(x,y)plt.xlabel('step')plt.ylabel('cpu time (s)')plt.savefig('1.png')np.savetxt("1.csv",y,delimiter=",",header='cpu time (s)',fmt='%s')
