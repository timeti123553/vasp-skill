#===============================================================================
# 参考脚本（原样收集 · 未验证 · 未运行）
# 来源文章: articles/20261001-VASP_vaspkit_STM_模拟.md
# 原文链接: https://zhuanlan.zhihu.com/p/667558468
# 用途    : 把 STM_*.jpg 按文件名里的高度排序、加红字标注，合成 STM_animation.gif
# 依赖    : Python + Pillow
# 功能说明: workflows.md 第十九节 / scripts/README.md 的 post/stm_frames.py（planned）（本目录只放源码文本，说明以那里为准）
# 抓取质量: 原文把脚本压成一整行（空格与换行全丢），只能读逻辑。
#===============================================================================
fromPILimportImage,ImageDraw,ImageFontimportglobimportre# 文件路径模式file_pattern="./STM_*.jpg"# 收集所有图片文件路径image_files=sorted(glob.glob(file_pattern))print(f"找到了 {len(image_files)} 个文件。")# 打开图片并追加到列表中images=[]forimage_fileinimage_files:print(f"处理文件：{image_file}")# 从文件名提取数字match=re.search(r'STM_([\d\.]+).jpg',image_file)ifmatch:number=match.group(1)print(f"提取到数字：{number}")# 打开图片try:original_img=Image.open(image_file)exceptIOError:print(f"无法打开图片：{image_file}")continue# 创建一个小尺寸的画布用于绘制文字text_canvas=Image.new('RGBA',(170,170),(255,255,255,0))draw=ImageDraw.Draw(text_canvas)# 使用默认字体font=ImageFont.load_default()# 在小画布上绘制文本draw.text((10,10),number,font=font,fill="red")# 将小画布缩放到原始图片的尺寸text_canvas=text_canvas.resize(original_img.size,Image.Resampling.LANCZOS)# 将缩放后的文字画布与原始图片合并combined_img=Image.alpha_composite(original_img.convert('RGBA'),text_canvas)# 将修改后的图片添加到列表中images.append(combined_img)else:print(f"文件名不符合预期格式：{image_file}")# 如果找到了图片，则创建 GIFifimages:output_gif_path="./STM_animation.gif"# 增加每帧的持续时间frame_duration=500# 毫秒images[0].save(output_gif_path,save_all=True,append_images=images[1:],loop=0,duration=frame_duration)print(f"GIF 已创建: {output_gif_path}")else:print("没有图片可以创建 GIF。")
