import os
import argparse
import re
from PIL import Image

def get_natural_key(text):
    """
    用于自然排序的辅助函数
    将字符串中的数字部分转换为整数，这样 'img2.jpg' 就会排在 'img10.jpg' 前面
    """
    return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]

def convert_images_to_pdf(source_folder, output_pdf_name):
    """
    读取目录下的图片并合并为PDF
    :param source_folder: 图片所在的文件夹路径
    :param output_pdf_name: 输出的PDF文件名 (例如 result.pdf)
    """
    
    # 1. 获取该目录下所有文件
    if not os.path.exists(source_folder):
        print(f"错误: 文件夹 '{source_folder}' 不存在")
        return

    files = os.listdir(source_folder)
    
    # 2. 过滤图片文件 (支持 jpg, png, jpeg, bmp 等)
    supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    image_files = [f for f in files if f.lower().endswith(supported_extensions)]
    
    if not image_files:
        print("未在该目录下找到图片文件。")
        return

    # 3. 按文件名进行自然排序
    image_files.sort(key=get_natural_key)
    print(f"检测到 {len(image_files)} 张图片，正在处理...")
    print(f"排序后的首张图片: {image_files[0]}")

    image_list = []
    first_image = None

    for filename in image_files:
        path = os.path.join(source_folder, filename)
        try:
            img = Image.open(path)
            
            # 4. 格式转换: PDF 需要 RGB 模式
            # 如果是 PNG 等带有透明通道(RGBA)的图片，需要转为 RGB，否则会报错或背景变黑
            if img.mode == 'RGBA':
                # 创建一个白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                # 将原图粘贴到白底上（使用原图alpha通道作为mask）
                background.paste(img, mask=img.split()[3]) 
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            if first_image is None:
                first_image = img
            else:
                image_list.append(img)
                
        except Exception as e:
            print(f"跳过无法处理的文件 {filename}: {e}")

    # 5. 保存 PDF
    if first_image:
        try:
            # save_all=True 表示保存多页，append_images 放入剩余图片
            first_image.save(output_pdf_name, "PDF", resolution=100.0, save_all=True, append_images=image_list)
            print(f"成功！PDF 已保存为: {os.path.abspath(output_pdf_name)}")
        except Exception as e:
            print(f"保存 PDF 时出错: {e}")
    else:
        print("没有可用的图片被处理。")

# ================= 配置区域 =================
if __name__ == "__main__":
    # # 修改这里：图片所在的文件夹路径
    # # '.' 代表当前目录，也可以写绝对路径，如 'C:/Photos/'
    # input_dir = './my_images' 
    # 
    # # 修改这里：输出的文件名
    # output_filename = 'output.pdf'

    parser = argparse.ArgumentParser(description="将指定文件夹下的图片合并为一个PDF文件。")
    parser.add_argument('--input_dir', '-i', type=str, required=True, help='图片所在的文件夹路径')
    parser.add_argument('--output', '-o', type=str, default='output.pdf', help='输出的PDF文件名，默认为 output.pdf')

    args = parser.parse_args()
    input_dir = args.input_dir
    output_filename = args.output



    convert_images_to_pdf(input_dir, output_filename)
