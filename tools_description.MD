# 工具描述

本文档汇总了 scLego 平台全部工具的核心功能、关键参数与输出内容。所有模块按照使用场景分为 **SC（单细胞）** 与 **ST（空间转录组）** 两大类，并沿用了统一的模板结构，方便查询与比对。

## SC 工具

### loadData (Alias 1_0)

#### 描述
汇集 Cell Ranger 输出或已建 Seurat/RDS 对象，自动识别表达矩阵、特征与条码信息，并补充样本/分组等元数据，生成统一格式的起始对象。

#### 参数
1. Species：物种信息，`c("hs", "mm")`。
2. MultiCR：Cell Ranger 目录结构选择，`TRUE`（`cr_path/sample_name/count/sample_filtered_feature_bc_matrix`）或 `FALSE`（`cr_path/1_GEX/sample_name/outs/filtered_feature_bc_matrix`）。
3. custom_rds_arg：可选上传自定义 Seurat 对象的路径、对象名及样本/组元数据列配置。

#### 输出
1. 运行成功与否状态。
2. `Rdata/0-Data_RawObject_addMeta.rds` 及对应的 `sample_meta` 和日志文件。

### qcData (Alias 1_1)

#### 描述
依据线粒体比例、血红蛋白比例、基因/UMI 复杂度等指标评估单细胞质量，按阈值剔除低质量细胞并输出质控前后对比图，确保后续分析基于可靠数据。

#### 参数
1. Species：物种决定线粒体、血红蛋白基因前缀，`c("hs", "mm")`。
2. obj_name：输入 RDS 名称，默认 `0-Data_RawObject_addMeta.rds`。
3. qc_*：成组阈值（`qc_nFeature_RNA_min/max`、`qc_nCount_RNA_min/max`、`qc_percent.mt_min/max`、`qc_percent.hb_max`、`qc_log10GenesPerUMI_min`、`qc_nCell_Feature_min`）以及 `qc_run` 是否执行过滤。

#### 输出
1. `Rdata/1-Data_QualityControl.rds`。
2. `Img/` 质控前后小提琴图和 `Stat/` QC 汇总。

### preprocessData (Alias 1_2)

#### 描述
执行标准化、筛选高变基因、回归指定协变量并缩放表达矩阵，生成稳定的表达基础和高变特征列表，供降维与聚类复用。

#### 参数
1. normalization：`normalization_run`、`normalization.method`（`LogNormalize/CLR/RC`）与 `scale.factor`。
2. feature_selection：`feature_selection_run`、`selection.method`（`vst/mvp/disp`）与 `nfeatures`。
3. scale：`scale_run` 及 `vars_to_regress`（如 `percent.mt`）。

#### 输出
1. `Rdata/2-Data_preprocess.rds`。
2. 高变基因图 (`Img/1_2_major_HighVariableFeatures`) 与 `Stat/1_2_major_HighVariableGene.xlsx`。

### pcaData (Alias 1_3)

#### 描述
在高变基因上运行 PCA，产出细胞/特征的主成分嵌入，并通过 Elbow、JackStraw 等图评估可用于下游分析的主成分数量。

#### 参数
1. pca：`pca_run`、`npcs`、`JackStraw_run`、`Jack_num.replicate`、`Jackdims`、`Elbow_run`、`Elbow_ndims`。
2. obj_name：默认 `2-Data_preprocess.rds`。
3. Species/Tag：沿用前序配置，用于分组绘图。

#### 输出
1. `Rdata/3-Data_PCA.rds`。
2. `Img/` 下 PCA、Elbow、JackStraw 图及 `Stat/` 载荷、嵌入表。

### integrateData (Alias 1_4)

#### 描述
对多样本或多批次对象应用 Seurat Integration、Harmony、CCA、Azimuth 等整合策略，校正批次差异并形成统一的整合低维空间。

#### 参数
1. integrate_run：`TRUE/FALSE` 控制是否整合。
2. integrateLayer_method：整合算法（`cca`, `rpca`, `harmony`, `azimuth` 等）。
3. data_split_by：用于分批整合的元数据列名。

#### 输出
1. `Rdata/4-Data_Integration.rds`（或继承输入对象）。
2. `Img/` 中的整合 UMAP/TSNE 预览与 `Stat/` 参数记录。

### clusterReductionData (Alias 1_5)

#### 描述
在 PCA 空间上构建 KNN 图并执行图谱聚类，同时计算 UMAP、t-SNE 等可视化嵌入，输出细胞分群、降维散点图与关键参数记录。

#### 参数
1. FindNeighbors：`FindNeighbors_run`、`FindNeighbors_dims`、`k.param`、`nn.method/metric` 等。
2. FindClusters：`FindClusters_run`、`FindClusters_resolution`、`algorithm`、`group.singletons`。
3. RunUMAP/RunTSNE：`umap_dims`、`n.neighbors`、`min.dist`、`tsne.method`、`max_iter` 等降维配置。

#### 输出
1. `Rdata/5-Data_clusterReduction.rds`。
2. 聚类/降维散点图及对应的 `Stat/` 分群统计、参数 JSON。

### autoAnnotationData (Alias 1_6)

#### 描述
根据表达轮廓自动注释细胞类型，可使用 SingleR（多种参考库）或 angrycell（分层注释）方案，并生成混淆矩阵、雷达图等质量评估。

#### 参数
1. autoAnno_method：`singleR` 或 `angrycell`，并可通过 `angry_layers` 控制 angrycell 层数。
2. singleR_ref：SingleR 参考（`ImmGenData`, `HumanPrimaryCellAtlasData` 等），依据物种选择。
3. reduction_umap：用于注释的 UMAP 名称（`umap.unintegrated`, `umap.harmony`, …）。

#### 输出
1. `Rdata/6-Data_autoAnno.rds` 含自动注释列。
2. 注释雷达/热图、混淆矩阵与 `Stat/` 单元格统计。

### setFinalAnnoData (Alias 1_7)

#### 描述
综合自动注释与人工审阅，固化最终细胞标签，并可同时输出差异表达、通路富集以及 Loupe (`cloupe`) 等交付文件。

#### 参数
1. setFinalAnno：`finalAnno_choose`（选择使用的注释列）、`reduction_umap`。
2. deg：`deg_run`、`deg_set_celltype/group`、`logfc.threshold`、`min.pct`、`jjVolcano`。
3. enrich：`enrich_run`、`enrich_plot`、`gsea_run` 控制后续富集工作流。

#### 输出
1. `Rdata/7-Data_finalAnno.rds` 与（可选）`cloupe` 文件。
2. 差异/富集结果及对应图片。

### seu2omni (Alias 1_8)

#### 描述
将最终 Seurat 对象拆分为 OmniViewer/Omni-ATLAS 兼容的表达矩阵、元数据与配置文件，便于在外部平台继续浏览与分析。

#### 参数
1. obj_name：需转换的 RDS（默认 `7-Data_finalAnno.rds`）。
2. Species/Tag：写入元信息的基础字段。
3. 输出路径：继承 `system.data_source`。

#### 输出
1. Omni 兼容文件及必要的表达矩阵、注释表。
2. 运行日志与转化脚本输出。

### seu2omni (Python 版本，Alias 1_9)

#### 描述
在 Python/conda 环境下调用 Omni 转换流程，可在 HPC/Slurm 等计算环境中批量生成 Omni 标准结果。

#### 参数
1. input_output：`input_path`、`phase`、`method`、`tag`、`taxonomyID`。
2. basic：`conda_env`、`runner`、`image`、`command` 模版。
3. system：`project_path`、`common_dir`、`data_source`。

#### 输出
1. Omni 标准输出目录（含日志、表达矩阵、注释 JSON）。
2. 运行日志与转换结果。

### celltypist (Alias 1_opt_celltypist)

#### 描述
利用 CellTypist 预训练模型对细胞进行补充注释，可根据表达层级选择不同模型、执行多模型投票，并输出预测标签及概率矩阵。

#### 参数
1. method：`data_type`（原始/整合）、`data_assay`、`obj_name`。
2. celltypist_model：预训练权重名称，支持 `Immune_All_Low`, `Immune_All_High` 等。
3. majority_voting/over_clustering：控制是否进行多模型投票与过聚类模式；`plot_*` 字段指定绘图列。

#### 输出
1. 更新后的 RDS（含 CellTypist 注释列）及预测概率表。
2. `Img/` 投票结果、`Stat/` 注释矩阵。

### DecontX (Alias 1_opt_DecontX)

#### 描述
调用 Celda DecontX 对捕获到的环境 RNA 进行去噪，生成去污染后的表达矩阵与 Seurat 对象，降低背景信号对后续分析的影响。

#### 参数
1. system.cr_path / sample_meta_path：指定输入矩阵与样本信息。
2. input_output.Species：物种（`hs/mm`）与 `MultiCR` 结构说明。
3. output_path / method：结果输出目录与执行模式。

#### 输出
1. 去污染后的表达矩阵与 Seurat 对象。
2. 去除比例统计表与日志。

### moveDoublet (Alias 1_opt_moveDoublet)

#### 描述
封装 DoubletFinder、Scrublet 等算法检测潜在双细胞，可针对指定聚类或嵌入空间计算评分并选择性地移除可疑细胞。

#### 参数
1. moveDoublet_run：`TRUE/FALSE` 是否执行。
2. moveDoublet_method：算法选择（`doubletFinder`, `scrublet` 等）。
3. nPCs、annotation_cluster_used、reduction_umap：控制 PCA 数、参与的聚类列及降维空间。

#### 输出
1. 更新 RDS（含双细胞标记与过滤版本）。
2. 双细胞评分可视化与统计。

### velocyto (Alias 1_opt_velocyto)

#### 描述
整合 Velocyto/scVelo 生成的 RNA velocity，将速度矢量写回 Seurat 对象并投影到 UMAP/TSNE 等嵌入上，展示瞬时转录动力学。

#### 参数
1. Species/Tag：指定物种与输出前缀。
2. method：`phase`、`method`、输入对象/loom 文件路径。
3. pipeline：容器镜像、运行命令及所需环境配置。

#### 输出
1. 含 RNA velocity 信息的对象及投影图。
2. `Img/` velocity 流场、`Stat/` 参数记录。

### subclusterAnno (Alias 2_1)

#### 描述
针对指定主类细胞执行二次聚类与注释，支持批次校正、样本拆分与自动注释策略，用于解析更细粒度的亚群结构。

#### 参数
1. data_split_by / selectMajorCellType：声明子分析依据的元数据列与主类。
2. subAnnotation_run、resolution：控制是否运行及二次聚类粒度。
3. autoAnno_method、angry_layers、singleR_ref、batch_method：复用自动注释与批次整合配置。

#### 输出
1. 每个子群的 RDS、注释表与差异结果。
2. `Img/` 二次聚类 UMAP、`Stat/` 细分统计。

### subCtDegEnrich (Alias 2_2)

#### 描述
在子群层面开展差异表达与功能富集，并最终确认子群的注释标签，帮助阐明亚群间的表达与功能差异。

#### 参数
1. setFinalsubAnno：继承 `setFinalAnno` 逻辑的最终注释配置。
2. deg：`deg_run`、`deg_set_celltype/group`、阈值参数。
3. enrich：`enrich_run`、`gsea_run`、`enrich_plot` 控制富集类型。

#### 输出
1. 子群差异矩阵、富集表、火山图等。
2. 结果对象及参数 JSON。

### mergeAnnoData (Alias 3_0)

#### 描述
汇总 Phase1/Phase2 产生的最终对象，对齐元数据并保留来源标签，为所有 Phase3 高级分析提供统一输入。

#### 参数
1. phase1_final_rds_path / phase2_final_rds_path：输入对象路径。
2. method.phase/method：结果标签及输出目录。
3. Species、tag：元信息。

#### 输出
1. 合并后的 RDS 及样本/元数据映射表。
2. Merge 过程日志。

### Cytotrace (Alias 3_1_Cytotrace)

#### 描述
运行 CytoTRACE 推断细胞发育潜能，对每个群体计算分化得分和排序热图，快速洞察整体发育梯度。

#### 参数
1. celltype_info：指定分析的列（键值对）。
2. group/tag：区分样本或实验条件。
3. obj_name：默认 `7-Data_finalAnno.rds`。

#### 输出
1. CytoTRACE 分数表与排名热图。
2. score 可视化及导出的统计表。

### monocle2 (Alias 3_1_monocle2)

#### 描述
利用 Monocle2 构建拟时轨迹，可在单样本或整合对象模式下自定义起止节点，输出轨迹图和伪时间排序。

#### 参数
1. mode：`default`, `gene_short_name` 等运行模式。
2. celltype_info、group：限定分析子集。
3. start/end/spline：在脚本中通过 `group`/`celltype` 字段控制起止节点。

#### 输出
1. 轨迹图、伪时间曲线与 `Stat/` 伪时间矩阵。
2. Monocle cds 对象及参数日志。

### slingshot (Alias 3_1_slingshot)

#### 描述
使用 Slingshot 在 PCA/UMAP 等嵌入空间推断多分支轨迹，计算各 lineage 的伪时间并展示分支结构，适用于存在分叉的发育过程。

#### 参数
1. reduction：`pca`、`umap` 等嵌入。
2. start/end：轨迹起止 cluster 名称。
3. Species/group/celltype_info：控制输入集与参考注释。

#### 输出
1. Slingshot 主干图与分支伪时间表。
2. `Stat/` 中的 pseudotime、lineage 信息。

### velocity (Alias 3_1_velocity)

#### 描述
整合 Velocyto/scVelo 速度矩阵，在 Seurat 对象中写入速度矢量并可视化速度流场，用于评估瞬时转录方向与动力。

#### 参数
1. embedding：选择 `umap`、`tsne` 或自定义坐标。
2. splice_obj_file：速度对象文件名。
3. celltype_info/group/mode：用于分组绘图及细胞集过滤。

#### 输出
1. 速度向量投影图、速度流场及结果 RDS。
2. 速度统计表。

### CellChat (Alias 3_2_CellChat)

#### 描述
基于 CellChat 数据库分析细胞间配体-受体通讯网络，支持样本合并与分组比较，并生成环形图、热图等多种通讯可视化。

#### 参数
1. celltype_info：定义细胞类型列。
2. group_compare / group_split_by：控制实验组比较。
3. merge：`TRUE/FALSE` 是否合并样本。

#### 输出
1. 信号通路富集、气泡图、热图与 `Stat/` CCI 表。
2. `Rdata/` 保存 CellChat 对象。

### CellphoneDB (Alias 3_2_CellphoneDB)

#### 描述
调用 CellphoneDB 解析细胞-细胞通讯关系，可设置统计/简易模式及阈值，输出配体-受体矩阵与关联气泡图。

#### 参数
1. run_cpdb_mode：`cpdb_statistical_analysis`（默认）、`cpdb_simple_analysis`、`cpdb_degs_analysis`。
2. threshold / pvalue：过滤显著交互的阈值。
3. group_compare / group_split_by：按元数据列分组比较。

#### 输出
1. CellphoneDB 输出表（means/pvalues/significant_means）。
2. 结果可视化（热图、气泡图）与日志。

### NicheNet (Alias 3_2_NicheNet)

#### 描述
运行 NicheNet 推断配体-受体-靶基因链路，结合发送者/接收者细胞类型与对照条件，输出配体优先级与靶基因富集结果。

#### 参数
1. sender_celltype / receiver_type：指定信号来源与接收群。
2. group_name / group_ref：比较条件。
3. target_type：差异基因来源（DEG/Gene set）。

#### 输出
1. 配体优先级表、热图、环形图。
2. NicheNet 对象与统计表。

### SCENIC (Alias 3_3_Scenic)

#### 描述
按照 SCENIC/pyscenic 流程构建调控网络，输出 regulon AUC、motif 富集及二进制矩阵，可针对指定细胞类型做下采样分析。

#### 参数
1. celltype_info / celltype_key：限定分析列。
2. downsample_n：每类最大细胞数。
3. threads：并行线程数；group/tag 控制输出组织。

#### 输出
1. Regulon AUC 矩阵、排名热图、二进制矩阵。
2. 调控网络图与运行日志。

### CellModule (Alias 3_4_CellModule)

#### 描述
执行模块化共表达分析（如 WGCNA/拟时模块），在时间/样本/群体维度上识别模块并输出模块基因、模块特征值及趋势曲线。

#### 参数
1. mode：`time`, `sample`, `group` 等。
2. module_num：期望模块数量。
3. celltype_info、sub_celltype_info、sample/time_info：选择分析子集。

#### 输出
1. 模块基因列表、模块得分表。
2. 热图/趋势线与 RDS。

### CoVarNet (Alias 3_4_CoVarNet)

#### 描述
利用 CoVarNet 构建协同变异网络，比对不同样本或亚群的共变结构，输出协变量矩阵、网络边列表与模块统计。

#### 参数
1. K：社区数或邻近参数。
2. celltype_info、group、sample/subtype：分析范围。
3. method.obj_name：输入对象。

#### 输出
1. 网络边列表、模块统计表。
2. 可视化图（网络图、热图）。

### MetaProgram (Alias 3_4_MetaProgram)

#### 描述
识别 MetaProgram 共表达特征，汇总跨样本共享的表达模块，输出每个 MetaProgram 的基因集、样本分数与功能富集摘要。

#### 参数
1. assay：使用的 assay。
2. category/subcategory、group.by、sample：定义比较维度。
3. nfeature：每个模块的特征数。

#### 输出
1. MetaProgram 基因集、各样本分数。
2. 热图与富集摘要。

### hdWGCNA (Alias 3_4_hdWGCNA)

#### 描述
运行 hdWGCNA 构建高维 WGCNA 网络，聚焦指定细胞类型或子群，输出模块 membership、eigengene 及网络可视化。

#### 参数
1. celltype_info / sub_celltype_info：指定分析列。
2. reduction：使用的降维空间。
3. group/sample：跨样本比较配置。

#### 输出
1. 模块 membership、eigengene 表。
2. WGCNA 网络可视化与参数 JSON。

### inferCNV (Alias 3_5_inferCNV)

#### 描述
基于 inferCNV 推断单细胞拷贝数变异，可独立控制运行/评分/绘图阶段，并输出 CNV 热图、评分与参考对照信息。

#### 参数
1. run_steps：`run/score/plot` 布尔标记。
2. method：`sample_col`、`Select_Sample_all/Group`、`meta_col`、`ref`。
3. score_para：`sample_list_path`、`Input_dir`；cutoff、HMM 设置。

#### 输出
1. inferCNV 热图、CNV 区域表、评分结果。
2. 运行日志与参数文件。

### Asgard (Alias 3_6_Asgard)

#### 描述
调用 Asgard 免疫微环境分析，比较肿瘤与正常样本的细胞状态、信号活性和潜在治疗反应，输出 Asgard 评分矩阵与诊断图表。

#### 参数
1. Species、Tissue：物种与组织（`adipose/blood/...`）。
2. celltype_info / sample_info：键值对形式指定细胞类型列与样本列。
3. Group_cancer / Group_Normal：比较组名，`group_compare` 控制差异方式。

#### 输出
1. Asgard 分析报告、评分矩阵。
2. `Rdata/` Asgard 对象与日志。

### ScPharm (Alias 3_6_ScPharm)

#### 描述
整合药物数据库评估潜在疗法，可按 drug_response 或 pathway 模式计算药物敏感性排名、靶点富集和热图。

#### 参数
1. Type：分析模式（`drug_response`, `pathway` 等）。
2. cancer：样本标记；merge：是否合并样本。
3. method.obj_name：输入对象。

#### 输出
1. 药物排名、靶点富集、热图。
2. 报告与参数日志。

### scRepertoire (Alias 3_7_scRepertoire)

#### 描述
将 scRepertoire 的 TCR/BCR 重排信息与 scRNA 注释联动，展示克隆扩增、链配对及与表达谱的关联，适用于免疫库分析。

#### 参数
1. type：`TCR` 或 `BCR`。
2. group/sample/subtype：按实验组或病程比较克隆扩增。
3. method.obj_name：包含 TCR/BCR 元数据的 RDS。

#### 输出
1. 克隆频次表、扩增可视化、网络图。
2. 与表达矩阵关联的结果对象。

## ST 工具

以下章节与 SC 管线保持同样的阶段顺序，涵盖所有空间转录组工具。

### loadData (Alias st_1_0)

#### 描述
载入 Visium、stereo-seq, HD, xenisum 等空间平台数据，自动处理表达矩阵、分辨率与边界信息，输出 Seurat/h5ad 等对象。

#### 参数
1. Platform：平台标识（`visium`, `stereo`, `chips` 等）。
2. Species：`hs/mm`，影响基因集选择。
3. h5ad / bin_type / bin_size / boundary / segmentations / save_format：分别对应输入文件、分箱策略与输出格式。

#### 输出
1. 标准化的 ST 对象（Seurat/h5seurat/h5ad）。
2. 样本/ROI 元信息与日志。

### qcData (Alias st_1_1)

#### 描述
对空间数据执行 spot 过滤、基因/UMI 阈值与线粒体比例评估，并输出过滤前后的统计、空间分布与小提琴图。

#### 参数
1. Platform/Species/h5ad：继承 loadData 输出。
2. save_format：`seurat`、`h5seurat`、`h5ad`。
3. qc.*：`min_features`, `max_features`, `percent.mt` 等阈值设置（位于 `qc` 节）。

#### 输出
1. `Rdata/` 过滤后的对象，`Img/` 质控图。
2. QC 汇总 Excel。

### preprocessData (Alias st_1_2)

#### 描述
对空间数据做 Normalize、筛选高变基因、缩放等预处理，可选择 LogNormalize、SCTransform 等策略并输出高变基因图。

#### 参数
1. preprocessData：`normalization.method`、`scale.factor` 等标准化配置。
2. LogNormalize：针对 log 流程的额外参数。
3. Platform/Species/h5ad/save_format：I/O 设置。

#### 输出
1. 预处理对象及高变基因列表。
2. 可视化图（HVG、表达概览）。

### pcaData (Alias st_1_3)

#### 描述
计算空间表达矩阵的 PCA，生成主成分嵌入并提供 Elbow、JackStraw 等判定图，指导后续聚类与整合。

#### 参数
1. pca：`pca_run`、`npcs`、`JackStraw_run`、`Jackdims`、`Elbow_run`、`Elbow_ndims`。
2. Platform/Species/h5ad/save_format。
3. method.phase/method：输出目录命名。

#### 输出
1. PCA 对象、载荷与嵌入统计。
2. PCA/Elbow/JackStraw 图。

### integrateData (Alias st_1_4)

#### 描述
对多切片或多批次空间数据执行Harmony、CCA 等整合算法，校正批次效应并形成统一的整合低维表示。

#### 参数
1. integerate：`integrate_run`、`integrate_method`、`split.by`。
2. Platform/Species/h5ad/save_format。
3. method.*：输出目录设置。

#### 输出
1. 整合后的 ST 对象。
2. 整合降维可视化与统计表。

### clusterReductionData (Alias st_1_5)

#### 描述
在空间数据中运行 FindNeighbors/FindClusters、UMAP/t-SNE 等操作，可选 signature score 或 module score 计算，输出分群与降维可视化。

#### 参数
1. FindNeighbors/FindClusters：设置横向与纵向聚类参数。
2. RunUMAP/RunTSNE：降维参数，含 `metric`, `spread` 等。
3. RunScore：`score_run`、`method`、`db` 控制 signature scoring。

#### 输出
1. 聚类结果对象、UMAP/t-SNE 图与 score 热图。
2. 统计表与参数 JSON。

### BANKSY (Alias st_1_opt_banksy)

#### 描述
应用 BANKSY 空间聚类算法，结合表达与邻域特征识别空间社区，可灵活串联 PCA、Harmony 及不同降维结果。

#### 参数
1. banksy：`banksy_dims`, `neighbor_k`, `weight` 等算法参数。
2. pca/harmony/FindNeighbors/FindClusters/RunUMAP/RunTSNE：可选前处理设置。
3. Platform/Species/h5ad/save_format。

#### 输出
1. BANKSY 聚类标签与可视化。
2. 运行日志与参数记录。

### split (Alias st_1_opt_split)

#### 描述
将大型切片拆分为多个 ROI 或分块对象，可按网格或自定义 ROI 列表分割，便于针对不同区域独立分析。

#### 参数
1. Platform/Species/h5ad/save_format：输入对象。
2. method.phase/method/tag：输出命名。
3. 其它参数：拆分方式、ROI 尺寸、是否重新编号。

#### 输出
1. 拆分后的多份 ST 对象及 ROI 元数据。
2. ROI 预览图。

### spotclean (Alias st_1_opt_spotclean)

#### 描述
封装 SpotClean 算法校正 Visium 等平台的背景污染，可调节污染阈值、迭代次数与空间分辨率以提升表达准确性。

#### 参数
1. spotclean：`spotclean_run`、`background_percent`、`method` 等。
2. bin_size：在 Stereo/Slide 平台下的分辨率设置。
3. Platform/Species/h5ad/save_format。

#### 输出
1. 清理后的表达矩阵与对象。
2. 污染比例与校正摘要。

### labelTransfer (Alias st_2_1)

#### 描述
使用 label transfer 将 scRNA 注释迁移到空间数据，支持多种 assay 组合与下采样策略，输出每个 spot 的预测细胞类型及概率矩阵。

#### 参数
1. scRNA_assay / st_assay / st_layer：指定输入数据层。
2. sc_downSample_num：控制参考细胞的最大数量。
3. method.phase/method：输出命名。

#### 输出
1. ST 对象含预测 celltype 列。
2. 迁移概率矩阵与可视化。

### sciBet (Alias st_2_1_sciBet)

#### 描述
调用 sciBet 对空间数据快速注释，可使用内置或自定义参考矩阵，生成 spot 级标签及概率并提供可视化对比。

#### 参数
1. ref_source：`built_in` 或 `custom`（需提供 `ref_file_name`）。
2. ref_assay/query_assay：指定引用与目标 assay。
3. k：邻居数量。

#### 输出
1. 注释标签与概率表。
2. 对应热图/混淆矩阵。

### stScore (Alias st_2_1_stScore)

#### 描述
计算 stScore 空间特异分数，结合 scRNA marker 与空间坐标，在多种打分模式下输出 spot 级功能得分与热图。

#### 参数
1. stScore_method：`spotlight`, `nnls`, `custom` 等。
2. degSource / mks_database_filename：marker 来源。
3. angle、stRNA_assay、scRNA_assay、stRNA_barplot_col：绘图与输入设置。

#### 输出
1. 每个 Spot 的分数表与空间热图。
2. 打分统计与图片。

### SPOTlight (Alias st_2_2_SPOTlight)

#### 描述
运行 SPOTlight 执行空间细胞成分去卷积，结合 scRNA 参考和 marker AUC 筛选，输出细胞占比矩阵与可视化。

#### 参数
1. sc_assay/st_assay：输入 assay 名。
2. sc_downSample_num、sc_mks_minAUC：控制参考范围。
3. Platform/Species/bin_size：空间数据描述。

#### 输出
1. 成分比例矩阵、成分热图。
2. 可视化（堆叠柱/空间热图）。

### stRCTD (Alias st_2_2_stRCTD)

#### 描述
使用 RCTD 进行空间去卷积，可选择标准或双细胞模式并启用并行加速，输出细胞成分预测、置信度及空间热图。

#### 参数
1. sc_assay/st_assay/st_layer：输入矩阵。
2. UMI_min / UMI_min_sigma / fc_cutoff：Spot 过滤与基因阈值。
3. doublet_mode、max_cores、sample_select（dev 版本）等。

#### 输出
1. 细胞成分预测与置信度。
2. 结果图（空间热图、堆叠图）。

### stRedeconve (Alias st_2_2_stRedeconve)

#### 描述
以 Redeconve 算法进行空间去卷积，可选择多任务/单任务模式并限定细胞类型列表，生成 spot 级细胞组成及可视化。

#### 参数
1. sc_assay / st_assay。
2. redeconve_mode：`multi`、`basic` 等。
3. cellnames：需要保留的细胞类型列表。

#### 输出
1. 细胞组成矩阵与可视化。
2. 运行日志。

### Redeconve (Alias st_2_3_Redeconve)

#### 描述
对 Redeconve 结果进行区域级汇总，可设定阈值筛选高置信度 ROI，输出区域得分与统计图。

#### 参数
1. obj_name：输入 RDS/h5ad。
2. thresh：阈值过滤。
3. tag：输出命名。

#### 输出
1. ROI 成分统计表。
2. 图像与参数 JSON。

### BuildNicheAssay (Alias st_3_1_BuildNicheAssay)

#### 描述
构建空间邻域（Niche） assay，将邻近 spot 聚合为微环境单元，便于开展通讯或微环境富集分析。

#### 参数
1. celltype：用于聚合的注释列。
2. st_assay：空间表达层。
3. neighbors.k / niches.k：邻居与 niche 大小。

#### 输出
1. 新建 `Niche` assay（表达矩阵+元数据）。
2. Niche 预览图与统计。

### cellcharter (Alias st_3_1_cellcharter)

#### 描述
运行 cellcharter 识别空间社区结构，并比较不同样本或切片中的社区组成，可启用仅基于邻域拓扑的 proximity-only 模式。

#### 参数
1. assay：空间 assay 名。
2. celltype / group / sample / slice：分层统计设置。
3. proximity_only：`TRUE/FALSE`。

#### 输出
1. 社区标签、富集分析与可视化图。
2. 结果表（社区构成）。

### Redeconve (Alias st_3_1_Redeconve)

#### 描述
在指定 Niche 或 ROI 上再次运行 Redeconve，聚焦局部区域的细胞成分推断，验证关键区域的微环境构成。

#### 参数
1. obj_name、thresh：输入及阈值。
2. tag：输出命名。
3. method.phase/method：流程信息。

#### 输出
1. 区域级成分热图与统计表。
2. 运行日志。

### roidefine (Alias st_3_1_roidefine)

#### 描述
定义空间 ROI，可从 CSV 导入坐标或手工指定条码列表，并移除不需要的区域，为 ROI 定向分析提供准确边界。

#### 参数
1. roi_from_csv / csv_files_path：启用 CSV 自定义 ROI。
2. barcode_name / sample_select / remove_Unassigned_roi。
3. st_assay：需要截取的 assay。

#### 输出
1. ROI 注释表，并同步更新对象元数据。
2. ROI 预览图。

### CellChat2 (Alias st_3_2_CellChat2)

#### 描述
扩展版 CellChat，结合空间位置信息、不同技术平台与切片选择，比较空间区域之间的通讯差异并输出多种可视化。

#### 参数
1. celltype_info：细胞类型列。
2. group_compare / group_split_by / position_compare。
3. assay / slice / sample / technique / select_sample。

#### 输出
1. 空间 CellChat 报告（通讯网络、气泡图、径向图）。
2. CellChat 对象与统计表。

### CellphoneDB (Alias st_3_2_CellphoneDB)

#### 描述
在空间背景下运行 CellphoneDB，可按 ROI/microenvironment 分组并结合活性转录因子信息，输出空间通讯矩阵与可视化。

#### 参数
1. st_assay、celltype_info：输入设置。
2. microenvs_col：分区列名。
3. run_cpdb_mode、threshold、pvalue、group_compare/group_split_by。

#### 输出
1. CellphoneDB 标准输出。
2. 图像与统计表。

### SpaTrack (Alias st_3_3_SpaTrack)

#### 描述
利用 SpaTrack 追踪空间轨迹或迁移路径，预测细胞在组织中的潜在迁移方向，输出轨迹轨道图与热点区域图。

#### 参数
1. threads：并行线程。
2. Platform/Species/save_format。
3. spatrack：轨迹模型参数（步长、迭代次数等）。

#### 输出
1. 轨迹轨道图、热点区域图。
2. 轨迹数据表与日志。

### SpaGRN (Alias st_3_4_SpaGRN)

#### 描述
构建空间基因调控网络（SpaGRN），结合样本/切片/技术条件推断局部调控关系，输出网络模块与调控强度可视化。

#### 参数
1. assay / celltype / sample / slice / technique。
2. min_cells / min_counts / min_genes：过滤阈值。
3. Species：决定参考基因集。

#### 输出
1. SpaGRN 网络、模块与度量表。
2. 可视化（热图、网络图）与日志。
