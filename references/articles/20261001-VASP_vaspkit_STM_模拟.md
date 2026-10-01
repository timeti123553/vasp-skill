# VASP vaspkit STM 模拟

- 来源: `https://zhuanlan.zhihu.com/p/667558468`
- 类型: html
- 标签: 知乎, 本人文章, STM, VASPKIT, 后处理
- ⚠️ 抓取说明：本文代码块来自网页高亮组件，**空格/缩进在抓取时丢失**（如 `from PIL import Image` 变成 `fromPILimportImage`），**不要直接复制运行**，按逻辑重写。
- 正文字数: 6598

---
原文链接：

[qiqiphysics：利用vaspkit进行STM模拟](https://zhuanlan.zhihu.com/p/606466586)

注：本文在原文的基础上做了一些修改和补充。

如有错误，欢迎指正。

进行 STM 模拟的时候，先进行 VASP 的自洽计算（生成 CHGCAR 和 WAVECAR 文件），然后用 VASP 进行相关的 STM 模拟。

本文计算的材料是石墨烯：

## 所需工具

在计算之前所需要准备的一些软件：

- VASP（5.4.4）

- vaspkit（1.4.1）

- python（3.11）

## 自洽计算

需要准备的输入文件：

- INCAR

- POSCAR

- POTCAR（vaspkit 生成，PBE 泛函）

- KPOINTS（vaspkit 生成）

- 作业提交脚本

### INCAR

Global Parameters ISTART=1(Read existing wavefunction;if there)LREAL= .FALSE. (Projection operators: automatic)PREC= Normal (Precision level)LWAVE= .TRUE. (Write WAVECAR or not)LCHARG= .TRUE. (Write CHGCAR or not)ADDGRID= .TRUE. (Increase grid; helps GGA convergence)LORBIT=11 Electronic Relaxation ISMEAR=0(Gaussian smearing; metals:1)SIGMA= 0.05 (Smearing value in eV; metals:0.2)NELM=60(Max electronic SCF steps)NELMIN=6(Min electronic SCF steps)EDIFF= 1E-08 (SCF energy convergence; in eV)LVHAR= T

### POSCAR

Surf-mp-48 1.00000000000000 1.2344083195740001 -2.1380573715510001 0.0000000000000000 1.2344083195740001 2.1380573715510001 0.0000000000000000 0.0000000000000000 0.0000000000000000 12.0000000000000000 C 2 Direct 0.0000000000000000 0.0000000000000000 0.5000000000000000 0.3333329999917112 0.6666670000099160 0.5000000000000000

## STM 模拟

需要准备的输入文件：

- INCAR

- POSCAR（自洽计算复制）

- POTCAR（自洽计算复制）

- KPOINTS（自洽计算复制）

- CHGCAR（自洽计算生成）

- WAVECAR（自洽计算生成）

- 作业提交脚本

### INCAR

Global Parameters ISTART=1(Read existing wavefunction;if there)LREAL= .FALSE. (Projection operators: automatic)PREC= Normal (Precision level)LWAVE= .TRUE. (Write WAVECAR or not)LCHARG= .TRUE. (Write CHGCAR or not)ADDGRID= .TRUE. (Increase grid; helps GGA convergence)LORBIT=11 Electronic Relaxation ISMEAR=0(Gaussian smearing; metals:1)SIGMA= 0.05 (Smearing value in eV; metals:0.2)NELM=60(Max electronic SCF steps)NELMIN=6(Min electronic SCF steps)EDIFF= 1E-08 (SCF energy convergence; in eV)LVHAR= T ################新增参数##################LPARD= .TRUE. LSEPK= .FALSE. LSEPB= .FALSE. NBMOD= -3 EINT= -0.1 0.1

注：运行完该 VASP 任务会生成 PARCHG 文件。

### LPARD

默认值：LPARD = .FALSE.

LPARD 参数用于确定是否计算部分（能带或 k 点分解的）电荷密度。请注意，从 WAVECAR 文件中读取的轨道必须在先前的 VASP 运行中收敛。

### LSEPK

默认值：LSEPK = .FALSE.

将每个 k 点的电荷密度写入文件 PARCHG.*.nk（LSEPK=.TRUE.）或将它们合并为一个文件（LSEPK=.False.）。

### LSEPB

默认值：LSEPB = .FALSE.

指定是单独计算每个波段的电荷密度并将其写入文件 PARCHG.nb.*（LSEPB=.TRUE.），还是合并所有选定波段的电荷浓度并将其写至文件 PARCHG.ALLB.* 或 PARCHG 。

### NBMOD

默认值：NBMOD = -1

控制在计算带分解电荷密度时使用哪些带。 另外也检查 IBAND 和 EINT。

该整数变量可以采用以下值：

- >0 ：数组 IBAND 中的值的数量。 如果指定了 IBAND，则 NBMOD 将自动设置为正确的值（在这种情况下，不应在 INCAR 文件中手动设置 NBMOD）。

- 0 ：考虑所有能带来计算电荷密度，甚至考虑未占据的能带。

- -1 ：像平常一样计算总电荷密度。 如果没有给出其他内容，则这是默认值。

- -2 ：计算特征值在 EINT 指定范围内的电子的部分电荷密度。

- -3 ：与之前相同，但能量范围是相对于费米能量给出的。

### EINT

默认值：EINT = not set

指定用于评估带分解电荷密度中所需的部分电荷密度的带的能量范围。同时检查 NBMOD 和 IBAND 。

注：vaspkit 中的自动绘图功能需要打开。即使用命令vi ~/.vaspkit进入文件，修改参数为AUTO_PLOT .TRUE.。

使用 vaspkit 生成 STM 模拟的图片：

vsapkit 325 1 0.5 8 8

- 1：恒定高度模式（STM 模式选项）。

- 0.5：一般高度要接近材料表面，这里选择了 。

- 8 8：输入沿 a 和 b 方向的重复单位。

### PLOT. in

使用 vaspkit 第一次运行的时候生成 PLOT. in 文件可以重新自定义打印预设。

将 PLOT. in 中的某些参数更改为：

font_family='sans-serif'# string type (default: 'arial'). Options: 'fantasy','arial','sans-serif', 'monospace', 'cursive', 'serif', etc.# contour-related settingscolormap='RdBu'# string typ (default: 'jet'). Options: 'jet', 'hsv', 'viridis', 'gray', etc.contour_levels=5# integer type (default: 5).contour_limits=[0.0, 1.0]# float type (No default value).display_colorbar= .TRUE. # .TRUE. or .FALSE (default: .FLASE.).display_level_value= .TRUE. # .TRUE. or .FALSE (default: .FLASE.).display_contour= .FALSE. # .TRUE. or .FALSE (default: .FLASE.).colorbar_shrink= 0.5 # float type (default: 0.4).colorbar_orientation='vertical'# 'horizontal' or 'vertical' (default: 'horizontal')

之后，我们在使用 vaspkit 生成图片，就可以得到：

恒定高度模式

### 动态图

通过下面命令，我们可以同时输出不同高度的恒定高度模式：

vsapkit 325 2 0.5 2 0.2 8 8

0.5 2 0.2：高度范围 ，步长为 。

注：生成的高度在就截止了，这可能是程序的问题。

可能是程序的问题，我的 vaspkit 无法设置输出的图片的格式一个图片的长宽比例。因此，我需要写一个程序裁剪图片四周的空白：

fromPILimportImageimportosdefcrop_all_borders(image_path):try:# 打开图像文件img=Image.open(image_path)# 获取图像的像素数据img_data=img.load()# 获取图像的尺寸width,height=img.size# 查找左边界left=0forxinrange(width):ifany(img_data[x,y]!=(255,255,255)foryinrange(height)):left=xbreak# 查找右边界right=width-1forxinrange(width-1,-1,-1):ifany(img_data[x,y]!=(255,255,255)foryinrange(height)):right=xbreak# 查找上边界top=0foryinrange(height):ifany(img_data[x,y]!=(255,255,255)forxinrange(width)):top=ybreak# 查找下边界bottom=height-1foryinrange(height-1,-1,-1):ifany(img_data[x,y]!=(255,255,255)forxinrange(width)):bottom=ybreak# 裁剪图像，去除所有边界的空白cropped_img=img.crop((left,top,right+1,bottom+1))# 保存裁剪后的图像cropped_img.save(image_path)print(f"已裁剪图像 {image_path}")exceptExceptionase:print(f"无法处理图像 {image_path}: {e}")defmain():# 获取当前目录下的所有jpg文件current_directory=os.getcwd()jpg_files=[fileforfileinos.listdir(current_directory)iffile.endswith(".jpg")]# 遍历每个jpg文件并进行裁剪forjpg_fileinjpg_files:image_path=os.path.join(current_directory,jpg_file)crop_all_borders(image_path)if__name__=="__main__":main()

输出结果：

已裁剪图像 /XXX/STM_0.50.jpg 已裁剪图像 /XXX/STM_0.70.jpg 已裁剪图像 /XXX/STM_0.90.jpg 已裁剪图像 /XXX/STM_1.10.jpg 已裁剪图像 /XXX/STM_1.30.jpg 已裁剪图像 /XXX/STM_1.50.jpg

将裁剪的图片整合在一起生成动态图，对应的 Python 代码为：

fromPILimportImage,ImageDraw,ImageFontimportglobimportre# 文件路径模式file_pattern="./STM_*.jpg"# 收集所有图片文件路径image_files=sorted(glob.glob(file_pattern))print(f"找到了 {len(image_files)} 个文件。")# 打开图片并追加到列表中images=[]forimage_fileinimage_files:print(f"处理文件：{image_file}")# 从文件名提取数字match=re.search(r'STM_([\d\.]+).jpg',image_file)ifmatch:number=match.group(1)print(f"提取到数字：{number}")# 打开图片try:original_img=Image.open(image_file)exceptIOError:print(f"无法打开图片：{image_file}")continue# 创建一个小尺寸的画布用于绘制文字text_canvas=Image.new('RGBA',(170,170),(255,255,255,0))draw=ImageDraw.Draw(text_canvas)# 使用默认字体font=ImageFont.load_default()# 在小画布上绘制文本draw.text((10,10),number,font=font,fill="red")# 将小画布缩放到原始图片的尺寸text_canvas=text_canvas.resize(original_img.size,Image.Resampling.LANCZOS)# 将缩放后的文字画布与原始图片合并combined_img=Image.alpha_composite(original_img.convert('RGBA'),text_canvas)# 将修改后的图片添加到列表中images.append(combined_img)else:print(f"文件名不符合预期格式：{image_file}")# 如果找到了图片，则创建 GIFifimages:output_gif_path="./STM_animation.gif"# 增加每帧的持续时间frame_duration=500# 毫秒images[0].save(output_gif_path,save_all=True,append_images=images[1:],loop=0,duration=frame_duration)print(f"GIF 已创建: {output_gif_path}")else:print("没有图片可以创建 GIF。")

输出结果：

找到了 6 个文件。 处理文件：./STM_0.50.jpg 提取到数字：0.50 处理文件：./STM_0.70.jpg 提取到数字：0.70 处理文件：./STM_0.90.jpg 提取到数字：0.90 处理文件：./STM_1.10.jpg 提取到数字：1.10 处理文件：./STM_1.30.jpg 提取到数字：1.30 处理文件：./STM_1.50.jpg 提取到数字：1.50 GIF 已创建: ./STM_animation.gif

输出的动态图：
