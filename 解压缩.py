import os
import zipfile
#路径配置（按需修改即可）
source_dir = r"C:\Users\jump\Desktop\H-35（34）\CamScanner\temp"  #📂📂📂存放压缩包的源文件夹
output_root = r"C:\Users\jump\Desktop\联合村宅基地登记核实"  #📂📂📂解压后文件存放的目标根文件夹（可自行创建）
#确保目标根文件夹存在，不存在则自动创建
os.makedirs(output_root, exist_ok=True)
#批量解压主逻辑
#遍历源文件夹内的所有文件
for file_name in os.listdir(source_dir):
    #只筛选 .zip 格式的压缩包，忽略其他格式文件，不区分大小写
    if file_name.lower().endswith(".zip"):
        #拼接得到当前压缩包的完整绝对路径
        zip_full_path = os.path.join(source_dir, file_name)

        #提取压缩包的文件名（去掉.zip后缀），作为解压后的子文件夹名
        #目的：每个压缩包单独放一个文件夹，避免不同压缩包的同名文件互相覆盖
        extract_subdir = os.path.splitext(file_name)[0]
        extract_full_path = os.path.join(output_root, extract_subdir)
        os.makedirs(extract_full_path, exist_ok=True)

        print(f"正在解压：{file_name}")
        try:
            #打开压缩包
            with zipfile.ZipFile(zip_full_path, "r") as zip_file:
                #遍历压缩包里的每一个文件/文件夹
                for file_info in zip_file.infolist():
                    #修复中文文件名乱码核心步骤
                    #zip格式历史原因默认用cp437编码存储文件名，Windows中文环境下会乱码
                    #尝试用cp437读取后转gbk编码，还原正确的中文名称
                    try:
                        file_info.filename = file_info.filename.encode("cp437").decode("gbk")
                    except:
                        #极少数特殊编码解码失败时，保留原文件名，不中断程序
                        pass
                    #将当前文件解压到目标子文件夹
                    zip_file.extract(file_info, extract_full_path)
            print(f"✅ 解压完成：{file_name}")
        except Exception as e:
            # 压缩包损坏、密码保护等异常情况，打印错误并跳过，继续处理下一个
            print(f"❌ 解压失败：{file_name}，错误原因：{e}")

print("\n所有压缩包处理完毕！")