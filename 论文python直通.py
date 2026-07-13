# 本实验需要的数据为高程、坡度、距河流，距县城中心距离，人口密度变化、GDP变化，夜间灯光强度变化、植被覆盖度变化
# 其中高程、坡度、距河流，距县城中心距离定义为不会变化的自变量；其余数据定义为变化的自变量
# 故而需要对人口密度数据、GDP数据，夜间灯光强度数据、植被覆盖度数据进行栅格计算(用2020年tif数据-2000年tif数据：获取两年间的变化情况)
root_folder = r"D:\论文初稿数据python代码全解"#主文件夹（自已手动创建）📂
#⚡⚡⚡⚠️⚠️注意：主文件夹需要自行创建和命名，folder_1文件夹也需要自行创建并填入数据⚠️⚠️
#全局环境配置
import arcpy
import os
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
#全局路径配置📂📂📂...
folder_1 = os.path.join(root_folder, "folder_1")  # 放置原始数据（自已手动创建）📂
folder_2 = os.path.join(root_folder, "folder_2")  # 放置数据预处理结果📂
folder_3 = os.path.join(root_folder, "folder_3")  # 放置投影完成后的成果📂
folder_4 = os.path.join(root_folder, "folder_4")  # 放置按掩膜提取后的成果📂
folder_5 = os.path.join(root_folder, "folder_5")  # 放置重分类8类后的栅格数据📂
folder_6 = os.path.join(root_folder, "folder_6")  # 放置重分类3类后的栅格数据📂
folder_7 = os.path.join(root_folder, "folder_7")  # 放置计算后的栅格数据，用以制作转移矩阵📂
folder_8 = os.path.join(root_folder, "folder_8")  # 放置栅格转点操作后的点数据📂
folder_9 = os.path.join(root_folder, "folder_9")  # 放置三生空间重心数据📂
folder_10 = os.path.join(root_folder, "folder_10")  # 放置三生空间标准差椭圆📂
folder_11 = os.path.join(root_folder, "folder_11")  # 放置重心迁移模型数据📂
folder_12 = os.path.join(root_folder, "folder_12")  # 放置自变量数据📂
folder_13 = os.path.join(root_folder, "folder_13")  # 放置渔网及各类表格📂
#自动创建所有不存在的子文件夹
all_folders = [folder_1, folder_2, folder_3, folder_4, folder_5,
               folder_6, folder_7, folder_8, folder_9, folder_10,
               folder_11, folder_12, folder_13]
for fp in all_folders:
    if not os.path.exists(fp):
        os.makedirs(fp)
        print(f"自动创建文件夹📂：{fp}")
    else:
        print(f"文件夹📂{fp}已存在，跳过")
# 校验空间分析扩展许可
if arcpy.CheckExtension("Spatial") != "Available":
    raise Exception("错误❌❌❌：未检测到Spatial Analyst扩展许可，脚本终止运行")
# 读取参考栅格，统一坐标系与像元分辨率
ref_raster_path = os.path.join(folder_1, "土地利用2000.tif")
if not arcpy.Exists(ref_raster_path):
    raise Exception(f"错误❌❌❌：参考栅格 {ref_raster_path}📂 不存在，请检查文件")
#锁定全局输出范围
ref_desc = arcpy.Describe(ref_raster_path)
ref_sr = ref_desc.spatialReference
ref_cell_size = ref_desc.meanCellWidth
# 全局统一输出坐标系与像元大小
arcpy.env.outputCoordinateSystem = ref_sr
arcpy.env.cellSize = ref_cell_size
print(f"ℹ️全局坐标系已统一为：{ref_sr.name}，单位：{ref_sr.linearUnitName}")
print(f"ℹ️全局像元分辨率已统一为：{ref_cell_size} {ref_sr.linearUnitName}")
#步骤1：导出行政区边界
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤1：导出盐源县行政区边界")
env.workspace = folder_1
clip_area_begining = os.path.join(folder_2, "盐源县行政区边界.shp")
#判定结果文件是否存在，避免重复操作，浪费时间
if arcpy.Exists(clip_area_begining):
    print("ℹ️结果数据已存在，跳过步骤1")
else:
    clip_area_begin = "凉山彝族自治州_县.shp"  # ============需要自行填入============
    if not arcpy.Exists(clip_area_begin):
        raise Exception(f"错误：未找到边界文件 {clip_area_begin}")
    where_clause = "name='盐源县'"
    arcpy.conversion.ExportFeatures(clip_area_begin, clip_area_begining, where_clause)
    print("✅已成功导出盐源县行政区边界")
#步骤2：研究区批量裁剪原始栅格
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤2：研究区批量裁剪原始栅格")
#由于栅格文件的大小可能过大，需要先行手动创建一个合适的研究区（面要素），并用此研究区裁剪原栅格文件。
env.workspace = folder_1
reseach_area = "研究区.shp"             #============需要自行创建，自行填入============
if not arcpy.Exists(reseach_area):
    raise Exception(f"错误❌❌❌：未找到研究区面要素 {reseach_area}")
pretreatment_folder = folder_2
raster_list_raw = arcpy.ListRasters()
if not raster_list_raw:
    raise Exception("错误❌❌❌：原始数据文件夹未检测到任何栅格文件")
for original_raster in raster_list_raw:
    nameBG = os.path.splitext(original_raster)[0]
    pretreatment_raster = nameBG + "_研究区.tif"
    out_pretreatment_raster = os.path.join(pretreatment_folder, pretreatment_raster)
    #判定结果文件是否存在，避免重复操作，浪费时间
    if arcpy.Exists(out_pretreatment_raster):
        print("ℹ️结果数据已存在，跳过步骤2")
    else:
        # 裁剪出研究区范围的栅格数据
        outEBM = ExtractByMask(original_raster, reseach_area, "INSIDE")
        outEBM.save(out_pretreatment_raster)
        print(f"已裁剪：{original_raster}")
    print("✅全部原始栅格研究区裁剪完成")
#步骤3：栅格投影 + 盐源县边界掩膜提取
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤3：栅格投影 + 盐源县边界掩膜提取")
env.workspace = folder_2
target_sr = ref_sr
clip_area_finally = os.path.join(folder_3, "盐源县标准边界.shp")
if arcpy.Exists(clip_area_finally):
    print("ℹ️结果数据已存在，跳过边界投影")
else:
    arcpy.management.Project(clip_area_begining, clip_area_finally, target_sr)
    print("✅行政边界投影完成")
#检测文件是否存在
mask_output_dir = folder_4
raster_list_clip = arcpy.ListRasters()
if not raster_list_clip:
    raise Exception("错误❌❌❌：预处理文件夹未检测到任何栅格文件")
#进行按掩膜提取
for raster_name in raster_list_clip:
    name_begin = os.path.splitext(raster_name)[0]
    base_name = name_begin.replace("_研究区", "")
    # 投影栅格
    out_raster_name = base_name + "_投影后.tif"
    out_raster = os.path.join(folder_3, out_raster_name)
    if arcpy.Exists(out_raster):
        print("ℹ️结果数据已存在，跳过栅格数据投影")
    else:
        arcpy.management.ProjectRaster(raster_name, out_raster, target_sr)
    # 按盐源县边界掩膜提取
    out_Extra_name = base_name + "_盐源县_掩膜.tif"
    out_Extra = os.path.join(mask_output_dir, out_Extra_name)
    if arcpy.Exists(out_Extra):
        print("ℹ️结果数据已存在，跳过栅格数据投影")
    else:
        outExtractByMask = ExtractByMask(out_raster, clip_area_finally, "INSIDE")
        # 仅对土地利用栅格做0值转NoData，连续型栅格保留有效值
        if "土地利用" in raster_name:
            out_NoData = SetNull(outExtractByMask, outExtractByMask, "Value = 0")
            out_NoData.save(out_Extra)
        else:
            outExtractByMask.save(out_Extra)
        print(f"✅已处理：{raster_name}")
#释放临时对象🗑️🗑️🗑️
try:
    del outExtractByMask, out_NoData
except:
    pass
arcpy.ClearWorkspaceCache_management()
print("✅所有栅格投影与掩膜提取完成")
#步骤4：土地利用重分类（8类+3类三生空间）
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤4：土地利用重分类")
env.workspace = mask_output_dir
land_use_raster = arcpy.ListRasters("*土地利用*")
#检测文件是否存在
if not land_use_raster:
    raise Exception("错误❌❌❌：未检测到土地利用栅格文件")
arcpy.ClearWorkspaceCache_management()
#8类三生空间重分类
def reclassification():
    print("ℹ️执行8类三生空间重分类")
    print(f"待处理栅格：{land_use_raster}")
    for Tree_live_space in land_use_raster:
        name_begin_1 = os.path.splitext(Tree_live_space)[0]
        base_name_1 = name_begin_1.replace("_盐源县_掩膜", "")
        out_Tls_name = base_name_1 + "_盐源8三生.tif"
        out_Tls = os.path.join(folder_5, out_Tls_name)
        if arcpy.Exists(out_Tls):
            print("ℹ️结果数据已存在，跳过8类重分类")
        else:
            # 设置重分类规则
            remapString = "11 11;12 11;51 21;52 22;53 23;54 23;55 23;56 23;21 31;22 31;23 31;24 31;25 31;31 32;32 32;41 33;42 33;43 33;46 33;64 33;66 34"
            out_reclass = Reclassify(Tree_live_space, "Value", remapString, "DATA")
            out_reclass.save(out_Tls)
            print(f"✅完成8类重分类：{Tree_live_space}")
    return
#3类三生空间重分类
def reclassification_1():
    print("ℹ️执行3类三生空间重分类")
    for oly_Tree_space in land_use_raster:
        name_begin_2 = os.path.splitext(oly_Tree_space)[0]
        base_name_2 = name_begin_2.replace("_盐源县_掩膜", "")
        out_Tls_name_1 = base_name_2 + "_盐源3三生.tif"
        out_Tls_1 = os.path.join(folder_6, out_Tls_name_1)
        if arcpy.Exists(out_Tls_1):
            print("ℹ️结果数据已存在，跳过3类重分类")
        else:
            # 设置重分类规则
            remap = "11 1;12 1;51 2;52 2;53 2;54 2;55 2;56 2;21 3;22 3;23 3;24 3;25 3;31 3;32 3;41 3;42 3;43 3;46 3;64 3;66 3"
            out_reclass = Reclassify(oly_Tree_space, "Value", remap, "DATA")
            out_reclass.save(out_Tls_1)
            print(f"✅完成3类重分类：{oly_Tree_space}")
    return
#执行重分类
reclassification()
reclassification_1()
arcpy.ClearWorkspaceCache_management()
print("✅土地利用重分类全部完成")
#步骤5：三生空间转移矩阵栅格计算
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤5：三生空间转移矩阵栅格计算")
env.workspace = folder_5
#输出文件夹
out_calculation_folder = folder_7
move_path_1=os.path.join(out_calculation_folder, "土地转移_2000_2010.tif")
move_path_2=os.path.join(out_calculation_folder, "土地转移_2010_2020.tif")
move_path_3=os.path.join(out_calculation_folder, "土地转移_2000_2020.tif")
if arcpy.Exists(move_path_1) and arcpy.Exists(move_path_2) and arcpy.Exists(move_path_3):
    print("ℹ️结果数据已存在，跳过步骤5")
else:
    raster_2000_list = arcpy.ListRasters("*2000*")
    raster_2010_list = arcpy.ListRasters("*2010*")
    raster_2020_list = arcpy.ListRasters("*2020*")
    # 检测所有年份文件是否存在
    if not raster_2000_list or not raster_2010_list or not raster_2020_list:
        raise Exception("错误❌❌❌：未找到完整的2000/2010/2020年土地利用栅格")
    # 提取各年份数据
    raster_2000 = Raster(raster_2000_list[0])
    raster_2010 = Raster(raster_2010_list[0])
    raster_2020 = Raster(raster_2020_list[0])
    # 获取转移数据2000-2010
    calculate_2000_2010 = raster_2000 * 100 + raster_2010
    calculate_2000_2010.save(move_path_1)
    # 获取转移数据2010-2020
    calculate_2010_2020 = raster_2010 * 100 + raster_2020
    calculate_2010_2020.save(move_path_2)
    # 获取转移数据2000-2020
    calculate_2000_2020 = raster_2000 * 100 + raster_2020
    calculate_2000_2020.save(move_path_3)
# 释放工作空间栅格 / 矢量文件占用锁，清理内存缓存避免文件占用报错🗑️🗑️🗑️
arcpy.ClearWorkspaceCache_management()
print("✅转移矩阵栅格计算完成")
#步骤6：栅格转点 + 重心提取 + 标准差椭圆
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤6：三生空间栅格转点、重心与标准差椭圆提取")
env.workspace = folder_6
raster_list_3class = arcpy.ListRasters()
#检测所有年份文件是否存在#检测所有年份文件是否存在
if not raster_list_3class:
    raise Exception("错误❌❌❌：3类重分类文件夹未检测到栅格文件")
for raster_point in raster_list_3class:
    raster_base = os.path.splitext(raster_point)[0]
    name_first = raster_base.replace("_盐源3三生", "")
    print(f"ℹ️正在处理：{name_first}")
    #输出文件夹
    out_raster_to_point = folder_8
    #生产空间（Value=1）
    raster_only_value1 = SetNull(raster_point, raster_point, "Value <> 1")
    out_raster_point_1 = os.path.join(out_raster_to_point, name_first + "_生产点.shp")
    if arcpy.Exists(out_raster_point_1):
        print("ℹ️检测到结果文件已存在，跳过")
    else:
        arcpy.conversion.RasterToPoint(raster_only_value1, out_raster_point_1, "Value")  # 栅格转点
        arcpy.Delete_management(raster_only_value1)
    #统计点要素数量，无有效像元则跳过重心、椭圆计算防止脚本报错🗑️🗑️🗑️
    count_result = arcpy.GetCount_management(out_raster_point_1)
    if int(count_result[0]) == 0:
        print(f"⚠️⚠️⚠️警告：{name_first} 生产空间无有效像元，跳过后续计算")
        arcpy.Delete_management(out_raster_point_1)
    else:
        Output_FC_sc = os.path.join(folder_9, name_first + "_生产重心.shp")
        if(arcpy.Exists(Output_FC_sc)):
            print("ℹ️检测到结果文件已存在，跳过")
        else:
            arcpy.stats.MeanCenter(out_raster_point_1, Output_FC_sc)
        Output_FC_ellipse_sc = os.path.join(folder_10, name_first + "_生产椭圆.shp")
        if arcpy.Exists(Output_FC_ellipse_sc):
            print("ℹ️检测到结果文件已存在，跳过")
        else:
            arcpy.stats.DirectionalDistribution(out_raster_point_1, Output_FC_ellipse_sc,
                                                "1_STANDARD_DEVIATION")
    # 生活空间（Value=2）
    raster_only_value2 = SetNull(raster_point, raster_point, "Value <> 2")
    out_raster_point_2 = os.path.join(out_raster_to_point, name_first + "_生活点.shp")
    if arcpy.Exists(out_raster_point_2):
        print("ℹ️检测到结果文件已存在，跳过")
    else:
        arcpy.conversion.RasterToPoint(raster_only_value2, out_raster_point_2, "Value")
        arcpy.Delete_management(raster_only_value2)
    # 统计点要素数量，无有效像元则跳过重心、椭圆计算防止脚本报错
    count_result = arcpy.GetCount_management(out_raster_point_2)
    if int(count_result[0]) == 0:
        print(f"⚠️⚠️⚠️警告：{name_first} 生活空间无有效像元，跳过后续计算")
        arcpy.Delete_management(out_raster_point_2)
    else:
        Output_FC_sh = os.path.join(folder_9, name_first + "_生活重心.shp")
        if arcpy.Exists(Output_FC_sh):
            print("ℹ️检测到结果文件已存在，跳过")
        else:
            arcpy.stats.MeanCenter(out_raster_point_2, Output_FC_sh)
        Output_FC_ellipse_sh = os.path.join(folder_10, name_first + "_生活椭圆.shp")
        if arcpy.Exists(Output_FC_ellipse_sh):
            print("ℹ️检测到结果文件已存在，跳过")
        else:
            arcpy.stats.DirectionalDistribution(out_raster_point_2, Output_FC_ellipse_sh,
                                                "1_STANDARD_DEVIATION")
    # 生态空间（Value=3）
    raster_only_value3 = SetNull(raster_point, raster_point, "Value <> 3")
    out_raster_point_3 = os.path.join(out_raster_to_point, name_first + "_生态点.shp")
    if arcpy.Exists(out_raster_point_3):
        print("ℹ️检测到结果文件已存在，跳过")
    else:
        arcpy.conversion.RasterToPoint(raster_only_value3, out_raster_point_3, "Value")
        arcpy.Delete_management(raster_only_value3)
    # 统计点要素数量，无有效像元则跳过重心、椭圆计算防止脚本报错🗑
    count_result = arcpy.GetCount_management(out_raster_point_3)
    if int(count_result[0]) == 0:
        print(f"⚠️⚠️⚠️警告：{name_first} 生态空间无有效像元，跳过后续计算")
        arcpy.Delete_management(out_raster_point_3)
    else:
        Output_FC_st = os.path.join(folder_9, name_first + "_生态重心.shp")
        if arcpy.Exists(Output_FC_st):
            print("ℹ️检测到结果文件已存在，跳过")
        else:
            arcpy.stats.MeanCenter(out_raster_point_3, Output_FC_st)
        Output_FC_ellipse_st = os.path.join(folder_10, name_first + "_生态椭圆.shp")
        if arcpy.Exists(Output_FC_ellipse_st):
            print("ℹ️检测到结果文件已存在，跳过")
        else:
            arcpy.stats.DirectionalDistribution(out_raster_point_3, Output_FC_ellipse_st,
                                                "1_STANDARD_DEVIATION")
#释放工作空间栅格 / 矢量文件占用锁，清理内存缓存避免文件占用报错🗑️🗑️🗑️
arcpy.ClearWorkspaceCache_management()
print("✅✅✅三生空间点、重心、椭圆提取完成")
#步骤7：三生空间重心迁移模型
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤7：三生空间重心迁移模型构建")
env.workspace = folder_9
space_types = ["生产", "生活", "生态"]
for st in space_types:
    point_2000_list = arcpy.ListFeatureClasses(f"*2000*{st}*")
    point_2010_list = arcpy.ListFeatureClasses(f"*2010*{st}*")
    point_2020_list = arcpy.ListFeatureClasses(f"*2020*{st}*")
    #判定数据是否存在
    if not point_2000_list or not point_2010_list or not point_2020_list:
        print(f"⚠️⚠️⚠️警告：{st}空间重心文件不全，跳过迁移模型构建")
        continue
    #依次锁定文件
    point_2000 = point_2000_list[0]
    point_2010 = point_2010_list[0]
    point_2020 = point_2020_list[0]
    #输出位置
    out_merge = os.path.join(folder_11, f"{st}重心合并.shp")
    if arcpy.Exists(out_merge):
        print("ℹ️检测到结果文件已存在，跳过")
    else:
        arcpy.management.Merge([point_2000, point_2010, point_2020], out_merge)
    # 生成连续迁移轨迹线，按年份顺序保证方向正确
    out_move_model = os.path.join(folder_11, f"重心迁移_{st}.shp")
    if arcpy.Exists(out_move_model):
        print("ℹ️检测到结果文件已存在，跳过")
    else:
        arcpy.management.PointsToLine(out_merge,out_move_model,"","",
                                      "NO_CLOSE","CONTINUOUS")
        print(f"{st}空间重心迁移模型构建完成✅")
#释放工作空间栅格 / 矢量文件占用锁，清理内存缓存避免文件占用报错🗑️🗑️🗑️
arcpy.ClearWorkspaceCache_management()
print("✅✅✅所有重心迁移模型构建完成")
#步骤8：变化类自变量栅格计算（2020-2000）
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤8：计算各要素2000-2020年变化量")
env.workspace = folder_4
out_independent_variable_folder = folder_12
out_pop=os.path.join(out_independent_variable_folder, "人口密度变化.tif")
if arcpy.Exists(out_pop):
    print("ℹ️检测到人口密度变化文件已存在，跳过")
else:
    # 人口密度变化
    pop_2000_list = arcpy.ListRasters("*人口密度*2000*")
    pop_2020_list = arcpy.ListRasters("*人口密度*2020*")
    if pop_2000_list and pop_2020_list:
        density_of_population_2000 = Raster(pop_2000_list[0])
        density_of_population_2020 = Raster(pop_2020_list[0])
        changes_in_population_density = density_of_population_2020 - density_of_population_2000
        changes_in_population_density.save(out_pop)
        print("✅人口密度变化量计算完成")
    else:
        print("⚠️⚠️⚠️警告：未找到完整的人口密度2000/2020年数据，跳过")
# GDP变化
out_GDP=os.path.join(out_independent_variable_folder, "GDP变化.tif")
if arcpy.Exists(out_GDP):
    print("ℹ️检测到GDP变化文件已存在，跳过")
else:
    gdp_2000_list = arcpy.ListRasters("*GDP*2000*")
    gdp_2020_list = arcpy.ListRasters("*GDP*2020*")
    if gdp_2000_list and gdp_2020_list:
        GDP_2000 = Raster(gdp_2000_list[0])
        GDP_2020 = Raster(gdp_2020_list[0])
        GDP_change = GDP_2020 - GDP_2000
        GDP_change.save(out_GDP)
        print("✅GDP变化量计算完成")
    else:
        print("⚠️⚠️⚠️警告：未找到完整的GDP2000/2020年数据，跳过")
# 夜间灯光变化
light_2000_list = arcpy.ListRasters("*夜间灯光*2000*")
light_2020_list = arcpy.ListRasters("*夜间灯光*2020*")
out_light=os.path.join(out_independent_variable_folder, "夜间灯光变化.tif")
if arcpy.Exists(out_light):
    print("ℹ️检测到夜间灯光变化文件已存在，跳过")
else:
    if light_2000_list and light_2020_list:
        light_2000 = Raster(light_2000_list[0])
        light_2020 = Raster(light_2020_list[0])
        light_change = light_2020 - light_2000
        light_change.save(out_light)
        print("✅夜间灯光变化量计算完成")
    else:
        print("⚠️⚠️⚠️警告：未找到完整的夜间灯光2000/2020年数据，跳过")
# 植被覆盖度（FVC）变化
fvc_2000_list = arcpy.ListRasters("*2000*FVC*")
fvc_2020_list = arcpy.ListRasters("*2020*FVC*")
out_FVC=os.path.join(out_independent_variable_folder, "FVC变化.tif")
if arcpy.Exists(out_FVC):
    print("ℹ️检测到FVC变化文件已存在，跳过")
else:
    if fvc_2000_list and fvc_2020_list:
        FVC_2000 = Raster(fvc_2000_list[0])
        FVC_2020 = Raster(fvc_2020_list[0])
        FVC_change = FVC_2020 - FVC_2000
        FVC_change.save(out_FVC)
        print("✅植被覆盖度变化量计算完成")
    else:
        print("⚠️⚠️⚠️警告：未找到完整的FVC2000/2020年数据，跳过")
#释放工作空间栅格 / 矢量文件占用锁，清理内存缓存避免文件占用报错🗑️🗑️🗑️
arcpy.ClearWorkspaceCache_management()
print("✅✅✅变化类自变量计算完成")
#步骤9：距离类自变量计算（欧氏连续距离）
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤9：计算距县城中心、距河流连续距离栅格")
env.workspace = folder_1
center_list = arcpy.ListFeatureClasses("*中心*")
river_list = arcpy.ListFeatureClasses("*河流*")
shp_desc = arcpy.Describe(clip_area_finally)
shp_extent = shp_desc.extent
arcpy.env.extent = shp_extent               #设定输出范围
# 县城中心距离
out_center_distance=os.path.join(folder_12, "距县城中心距离.tif")
if arcpy.Exists(out_center_distance):
    print("ℹ️检测到距县城中心距离文件已存在，跳过")
else:
    if not center_list:
        print("⚠️⚠️⚠️警告：未找到县城中心要素，跳过距县城距离计算")
    else:
        # 投影点数据（其实我的数据时自己创建的点数据，坐标系抑制，完全可以直接取用）
        center_raw = center_list[0]
        center_proj = os.path.join(folder_3, "县城中心_投影.shp")
        arcpy.management.Project(center_raw, center_proj, ref_sr)
        # 生成连续距离栅格，单位为米
        dist_center = EucDistance(center_proj)
        dist_center_clip = ExtractByMask(dist_center, clip_area_finally)
        dist_center_clip.save(out_center_distance)
        print("✅距县城中心距离栅格生成完成")
# 河流距离
out_river_distance=os.path.join(folder_12, "距河流距离.tif")
if arcpy.Exists(out_river_distance):
    print("ℹ️检测到距河流距离文件已存在，跳过")
else:
    if not river_list:
        print("⚠️⚠️⚠️警告：未找到河流要素，跳过距河流距离计算")
    else:
        river_raw = river_list[0]
        river_proj = os.path.join(folder_3, "河流_投影.shp")
        arcpy.management.Project(river_raw, river_proj, ref_sr)
        dist_river = EucDistance(river_proj)
        dist_river_clip = ExtractByMask(dist_river, clip_area_finally)
        dist_river_clip.save(out_river_distance)
        print("✅距河流距离栅格生成完成")
#释放工作空间栅格 / 矢量文件占用锁，清理内存缓存避免文件占用报错🗑️🗑️🗑️
arcpy.ClearWorkspaceCache_management()
print("✅✅距离类自变量计算完成")
#步骤10：坡度提取与DEM整理
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤10：提取坡度与DEM自变量")
env.workspace = folder_4
out_declivity_folder = folder_12
try:
    dem_list = arcpy.ListRasters("*DEM*")
    if not dem_list:
        raise Exception("未找到DEM栅格文件")
    yyx_DEM = Raster(dem_list[0])
    # 提取坡度
    out_declivit = os.path.join(out_declivity_folder, "坡度.tif")
    if arcpy.Exists(out_declivit):
        print("ℹ️检测到坡度文件已存在，跳过")
    else:
        out_declivit_raster = Slope(yyx_DEM)
        out_declivit_raster.save(out_declivit)
        # 复制DEM到自变量文件夹
    out_DEM = os.path.join(out_declivity_folder, "DEM.tif")
    if arcpy.Exists(out_DEM):
        print("ℹ️检测到DEM文件已存在，跳过")
    else:
        arcpy.management.CopyRaster(yyx_DEM, out_DEM)
    print("✅坡度与DEM数据整理完成")
except Exception as e:
    print(f"❌❌❌错误：坡度/DEM处理失败 - {str(e)}")
#释放工作空间栅格 / 矢量文件占用锁，清理内存缓存避免文件占用报错🗑️🗑️🗑️
arcpy.ClearWorkspaceCache_management()
#步骤11：创建1km渔网并编号
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤11：创建1km渔网并赋值编号")
boundary_shp = clip_area_finally
temp_fishnet_full = os.path.join(folder_12, "临时_渔网.shp")
out_fishnet = os.path.join(folder_12, "渔网_1km.shp")
if arcpy.Exists(out_fishnet):
    print("ℹ️检查到渔网已存在，跳过")
else:
    # 读取边界数据范围
    desc = arcpy.Describe(boundary_shp)
    extent = desc.extent
    # 计算渔网原点（左下角）和Y轴正北方向
    origin_coord = f"{extent.XMin} {extent.YMin}"
    y_axis_coord = f"{extent.XMin} {extent.YMin + 100}"
    # 创建渔网
    arcpy.management.CreateFishnet(temp_fishnet_full, origin_coord, y_axis_coord,
                                   1000, 1000, 0,
                                   0, "",
                                   "NO_LABELS",boundary_shp,"POLYGON")
    # 按边界裁剪
    arcpy.analysis.Clip(temp_fishnet_full, boundary_shp, out_fishnet)
    # 清理临时文件🗑️🗑️🗑️
    arcpy.Delete_management(temp_fishnet_full)
    arcpy.ClearWorkspaceCache_management()
    print("✅渔网创建完成")
    # 添加编号字段并赋值
    arcpy.management.AddField(out_fishnet, "编号", "SHORT")
    initial_number = 1
    with arcpy.da.UpdateCursor(out_fishnet, "编号") as cursor:
        for row in cursor:
            row[0] = initial_number
            cursor.updateRow(row)
            initial_number += 1
    print("✅渔网编号赋值完成")
#步骤12：土地利用区域制表+自变量分区统计
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤12：区域制表与分区统计")
zone_fishnet = out_fishnet
zone_field = "编号"
table_output_folder = folder_13
#12.1土地利用栅格区域制表
print("ℹ️ℹ️土地利用栅格区域制表")
env.workspace = folder_5
landuse_config = {"土地利用2000_盐源8三生.tif": "土地利用2000_渔网.dbf",
                  "土地利用2020_盐源8三生.tif": "土地利用2020_渔网.dbf"}
for raster_name, out_table_name in landuse_config.items():
    if not arcpy.Exists(raster_name):
        print(f"警告：未找到 {raster_name}，跳过")
        continue
    out_table_path = os.path.join(table_output_folder, out_table_name)
    if arcpy.Exists(out_table_path):
        print("ℹ️表格已存在，跳过")
    else:
        TabulateArea(zone_fishnet, zone_field, raster_name, "Value", out_table_path)
        print(f"✅完成区域制表：{raster_name}")
#释放工作空间栅格 / 矢量文件占用锁，清理内存缓存避免文件占用报错🗑️🗑️🗑️
arcpy.ClearWorkspaceCache_management()
# 12.2自变量栅格分区统计（均值）
print("ℹ️ℹ️自变量栅格分区统计（平均值）")
env.workspace = folder_12
raster_list_indep = arcpy.ListRasters()
if not raster_list_indep:
    raise Exception("错误：自变量文件夹未检测到任何栅格文件")
print(f"ℹ️检测到 {len(raster_list_indep)} 个自变量栅格待处理")
zonal_table_list = []
for raster_name in raster_list_indep:
    base_name = os.path.splitext(raster_name)[0]
    out_table_name = f"{base_name}_分区统计.dbf"
    out_table_path = os.path.join(table_output_folder, out_table_name)
    #以表格显示分区统计
    ZonalStatisticsAsTable(zone_fishnet,zone_field,raster_name,out_table_path,
                           "DATA","MEAN")
    zonal_table_list.append(out_table_path)
    print(f"完成分区统计：{raster_name}")
#释放工作空间栅格 / 矢量文件占用锁，清理内存缓存避免文件占用报错🗑️🗑️🗑️
arcpy.ClearWorkspaceCache_management()
#步骤13：合并所有分区统计结果为终极总表
print("=" * 60)
print("ℹ️ℹ️ℹ️步骤13：合并所有自变量统计结果为总表")
if len(zonal_table_list) < 1:
    print("⚠️⚠️⚠️警告：无分区统计表，跳过总表合并")
else:
    #GDB存放总表，替代dbf格式，前面没有创建就出错了
    gdb_path = os.path.join(table_output_folder, "结果总表.gdb")
    if not arcpy.Exists(gdb_path):
        arcpy.CreateFileGDB_management(table_output_folder, "结果总表.gdb")
    #总表放在GDB内
    final_table_path = os.path.join(gdb_path, "自变量总表")
    #复制第一张表作为基底
    arcpy.CopyRows_management(zonal_table_list[0], final_table_path)
    #更改字段
    first_raster_name = os.path.splitext(os.path.basename(zonal_table_list[0]))[0].replace("_分区统计", "")
    arcpy.management.AlterField(final_table_path, "MEAN", first_raster_name, first_raster_name)
    #依次连接剩余表并重命名
    for table_path in zonal_table_list[1:]:
        #提取名称，如DEM_分区统计.dbf ———— 提取出“DEM”
        raster_name = os.path.splitext(os.path.basename(table_path))[0].replace("_分区统计", "")
        #连接字段
        arcpy.management.JoinField(final_table_path, "编号", table_path, "编号", ["MEAN"])
        #更改字段名（GDB格式下AlterField可正常使用）
        arcpy.management.AlterField(final_table_path, "MEAN", raster_name, raster_name)
    # 清理冗余字段🗑️
    keep_fields = ["编号"] + [os.path.splitext(os.path.basename(t))[0].replace("_分区统计", "")
                              for t in zonal_table_list]
    for field in arcpy.ListFields(final_table_path):
        if not field.required and field.name not in keep_fields:
            arcpy.DeleteField_management(final_table_path, field.name)
    print(f"✅终极自变量总表已生成：{final_table_path}")
    print(f"ℹ️共包含 {len(keep_fields) - 1} 个自变量字段")
# 释放工作空间缓存
arcpy.ClearWorkspaceCache_management()
print("=" * 60)
print("🎉🎉🎉🎉 所有数据处理流程全部执行完成！")
print(f"ℹ️土地利用区域制表结果：{folder_13}")
print(f"ℹ️自变量分区统计结果：{folder_13}")
print(f"ℹ️合并后总表：{os.path.join(table_output_folder, '结果总表.gdb\\自变量总表')}")
print("完结撒花🎆🎆🎆👏👏👏")
#经检查，所得总表缺失标号为4076的数据，故而需要将土地利用数据的4076编号处删除；多了编号为7551的数据，故而需要删除
