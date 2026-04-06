# RuralBrain 下一阶段开发规划

> **规划版本**: v2.4
> **制定日期**: 2026-03-13
> **更新日期**: 2026-04-05
> **目标版本**: v0.1
> **预计周期**: 7 周

---

## 一、五大目标概述

| 目标 | 优先级 | 核心价值 |
|------|--------|----------|
| 1. 多模态大模型（Qwen3.5/3.6）集成 | ⭐⭐⭐ | 增强图片分析和多模态理解能力 |
| 2. 网络搜索功能 | ⭐⭐⭐ | 让 Agent 自主获取实时信息 |
| 3. 用户体验增强 | ⭐⭐⭐ | 前端 Demo 卡片一键触发 + 差异化交互 |
| 4. 生图模型集成（图文科普） | ⭐⭐ | 增强回答可视化，图解科普病症/疗法 |
| 5. 独立功能入口集成 | ⭐⭐ | 乡村经营、规划方案、法律助手（外部服务跳转） |
| 6. v0.1 版本部署 | ⭐⭐⭐ | 生产环境可用 |

### 新增需求说明（Week 3 周五）

| 需求 | 具体内容 | 技术要点 |
|------|----------|----------|
| **前端 Demo 卡片完善** | 各功能一键触发 Demo | 为每个 Skill 创建预设示例，点击自动填充输入 |
| **模型分级选择** | qwen3.5-flash 用于简单任务 | 复杂推理用 plus，固定工作流用 flash，降低成本 |
| **生图模型接入** | qwen-image-2.0 文生图科普 | 病症诊断后生成图解，类似 nano banana 科普博客 |
| **Qwen3.6 适配** | 升级到更强模型 | https://qwen.ai/blog?id=qwen3.6 能力增强 |

---

## 二、团队成员与专长

| 成员 | 核心专长 | 备注技能 |
|------|----------|----------|
| **A** | Agent 架构 & Skills 系统 | 全栈开发 |
| **B** | RAG & 规划咨询 | 全栈开发 |
| **C** | 部署 & 检测 & 定价 | 全栈开发 |
| **D** | 巡检 & 疾病预测 | 全栈开发 |

---

## 三、重要说明：外部服务集成

**三个外部服务**：乡村经营、规划方案、法律助手由外部团队独立开发，是完整的前后端项目。

**我们的工作**：在前端添加跳转按钮/入口，点击后跳转到对应的外部部署地址。

---

## 四、分阶段任务分配

### 阶段一：基础设施（Week 1-2）

#### 目标
完成多模态模型集成和网络搜索功能，增强现有工具的多模态能力。

#### 任务清单

| 任务 | 负责人 | 工作量 | 依赖 | 状态 |
|------|--------|--------|------|------|
| **A1: qwen3.5-plus 模型集成** | A | 3天 | - | ✅ 已完成 |
| - 扩展 `src/config.py` 模型配置 | | | | ✅ |
| - 实现 `src/utils/multimodal_message.py` 多模态消息构建 | | | | ✅ |
| - 测试多模态消息处理 | | | | ✅ |
| **A2: 网络搜索工具开发** | A | 3天 | - | ✅ 已完成 |
| - 实现 `src/agents/tools/web_search_tool.py` | | | | ✅ |
| - 创建 `src/agents/skills/configs/web_search.yaml` | | | | ⏭️ 已注册到工具加载器（无需单独 YAML） |
| - 注册到工具加载器 | | | | ✅ |
| **B1: RAG 与搜索融合** | B | 2天 | A2 | ✅ 已完成 |
| - 在 `planning.yaml` 中集成搜索工具 | | | | ✅ |
| - 实现混合检索策略（向量+BM25） | | | | ✅ `hybrid_retriever.py` |
| - 优化检索结果排序 | | | | ✅ |
| - 联网搜索补充功能 | | | | ✅ `enable_web_search` 参数 |
| **C1: 定价工具集成搜索** | C | 2天 | A2 | ✅ 已完成 |
| - 修改 `pricing_tool.py` 调用搜索获取实时价格 | | | | ✅ `_search_realtime_price()` |
| - 实现搜索结果过滤和验证 | | | | ✅ |
| - 对比本地知识库和网络价格 | | | | ✅ |
| **C2: 检测多模态增强** | C | 2天 | A1 | ✅ 已完成 |
| - 检测工具支持多模态消息提取 base64 图片 | | | | ✅ |
| - 检测结果用 Qwen 生成自然语言解释 | | | | ✅ `generate_detection_explanation()` |
| - 提供处理建议和预防措施 | | | | ✅ |
| - 增强前端展示 | | | | ❌ 待实现 |
| **D1: 巡检图片分析增强** | D | 2天 | A1 | ✅ 已完成 |
| - `farm_inspection_tool` 支持多图片输入 | | | | ✅ |
| - Qwen-VL 综合分析多张巡检照片 | | | | ✅ |
| **D2: 疾病预测多模态** | D | 2天 | A1 | ✅ 已完成 |
| - `disease_prediction_tool` 支持图片 + 症状文本 | | | | ✅ |
| - 多模态输入提高预测准确性 | | | | ✅ |

#### 里程碑
- [x] Agent 支持多模态输入（`build_multimodal_message` + 测试覆盖）
- [x] Agent 可以联网搜索（Tavily API 集成）
- [x] RAG 系统支持混合检索（向量 + BM25，`hybrid_retriever.py`）
- [x] 定价工具支持实时价格查询（`_search_realtime_price()`）
- [x] 检测服务支持智能解释（`generate_detection_explanation()`）
- [x] 巡检和疾病预测支持多模态（D1 + D2 已完成）

---

### 阶段二：用户体验（Week 3-4）

#### 目标
优化前端 UI，体现与通用 AI 的差异化特色。

#### 与通用 AI 的差异化体现

| 维度 | 具体体现 | 验收标准 |
|------|----------|----------|
| **工具可视化** | 用户看到 Agent 调用了哪些工具 | 每次工具调用有名称、图标、状态、结果摘要 |
| **知识溯源** | 回答标注知识来源 | RAG 检索结果显示文档名、页码、置信度 |
| **专业深度** | 乡村领域专用工具 | 巡检报告、疾病预测、定价分析有专业格式 |
| **多模态协同** | 图片 + 知识库 + 搜索 | 图片问题调用检测工具，同时检索知识库，给出综合建议 |

#### UI 具体优化点

```
欢迎界面 → 展示 4 大能力卡片 + 外部服务入口
工具调用 → 左侧显示工具链路，右侧显示对话结果
知识来源 → 检索结果折叠面板，可展开查看来源
检测结果 → 标注框 + 置信度 + 问题描述 + 处理建议
```

#### 任务清单

| 任务 | 负责人 | 工作量 | 依赖 | 状态 |
|------|--------|--------|------|------|
| **B2: 前端 UI 风格优化** | B | 3天 | 阶段一 | ✅ 已完成 |
| - 重新设计欢迎界面（4 大能力卡片） | | | | ✅ 核心+商业+规划+外部服务 |
| - 创建工具调用可视化组件 | | | | ✅ `ToolCallDisplay` + `tool-icons.ts` |
| - 知识库来源展示优化（可展开面板） | | | | ✅ `KnowledgeSourceDisplay` |
| **B3: RAG 与搜索融合测试** | B | 1天 | B1 | ✅ 已完成 |
| - 检索器单元测试 | | | | ✅ `test_rag_retriever.py` |
| - A/B 测试混合检索策略 | | | | ✅ `test_hybrid_ab.py` |
| - 优化检索结果排序权重 | | | | ✅ 推荐 `bm25_dominant` 配置 |
| **A7: Qwen-VL 技术预研** | A | 1天 | A1 | 待开始 |
| - 研究视频输入能力（为未来巡检视频做准备） | | | | |
| - 多图对比分析能力探索 | | | | |
| - 输出技术预研报告和最佳实践文档 | | | | |
| **A8: 工具性能优化** | A | 2天 | 阶段一 | 待开始 |
| - 分析现有工具调用性能瓶颈 | | | | |
| - 优化多模态输入的响应时间 | | | | |
| - 实现工具调用缓存机制 | | | | |
| **A10: Qwen3.6 模型适配** ⭐新增 | A | 1天 | - | 待开始 |
| - 更新 `src/config.py` 添加 qwen3.6 配置 | | | | |
| - 测试 Qwen3.6 多模态能力增强点 | | | | |
| - 对比 plus vs 3.6 性能和成本 | | | | |
| **A11: 模型分级选择机制** ⭐新增 | A | 2天 | A10 | 待开始 |
| - 设计任务复杂度判断规则 | | | | |
| - 实现 `ModelSelector` 类（plus/flash 自动切换） | | | | |
| - 配置 Skill 级别模型偏好（固定工作流用 flash） | | | | |
| - 测试成本降低效果（目标降低 30%+） | | | | |
| **B5: 前端 Demo 卡片完善** ⭐新增 | B | 2天 | B2 | ✅ 已完成 |
| - 为每个 Skill 创建预设 Demo 示例 | | | | ✅ `demo-cards.ts` 11个卡片 |
| - 实现一键触发功能（点击自动填充输入） | | | | ✅ `handleDemoClick` + 图片自动加载 |
| - Demo 示例涵盖：检测、定价、巡检、疾病预测、规划咨询 | | | | ✅ |
| - 添加 Demo 卡片动画效果 | | | | ✅ hover光效 + 渐变动画 |
| **D3: 前端体验优化** | D | 2天 | - | 待开始 |
| - 移动端响应式适配 | | | | |
| - 工具调用动画效果 | | | | |
| - 加载状态优化 | | | | |
| **D4: 工具可视化增强** | D | 3天 | 阶段一 | 待开始 |
| - 检测结果标注展示（标注框 + 置信度） | | | | |
| - 巡检报告可视化 | | | | |
| - 疾病预测结果图表 | | | | |
| **A9: 文档完善** | A | 1天 | 阶段一 | 待开始 |
| - 更新 API 文档（新增多模态和搜索接口） | | | | |
| - 完善开发者指南（环境配置、调试技巧） | | | | |
| - 编写故障排查手册 | | | | |

#### 里程碑
- [x] 差异化 UI 设计完成（4 大能力卡片）
- [ ] 移动端适配完成
- [x] 工具调用可视化上线
- [x] 知识溯源功能上线
- [x] RAG 混合检索策略优化完成（A/B 测试已完成，推荐 `bm25_dominant` 配置）
- [ ] Qwen-VL 技术预研报告完成
- [ ] 工具性能优化完成（响应时间提升 30%+）
- [ ] API 文档和故障排查手册完善
- [ ] ⭐新增：Qwen3.6 模型适配完成
- [ ] ⭐新增：模型分级选择机制上线（plus/flash 自动切换）
- [x] ⭐新增：前端 Demo 卡片一键触发功能上线
- [ ] ⭐新增：前端 Demo 卡片一键触发功能上线

---

### 阶段三：功能入口集成 + 生图模型（Week 5-6 第1-3天）

#### 目标
1. 在前端添加三大外部服务的快捷入口，实现服务间跳转
2. ⭐新增：集成 qwen-image-2.0 生图模型，实现图文科普功能

#### ⚠️ 重要时间说明
**阶段三在 Week 6 只占用前 3 天**，剩余 2 天为阶段四的部署预演任务预留。

#### 重要说明

**三个外部服务说明**：
- **乡村经营**、**规划方案**、**法律助手** 由外部团队独立开发，是完整的前后端项目
- 我们的工作：在前端添加跳转按钮/入口，点击后跳转到对应的外部部署地址
- 不需要开发这些服务的具体功能

**⭐ 生图模型集成说明**：
- **qwen-image-2.0** / **qwen-image-2.0-pro** 用于生成图解科普内容
- 典型应用：疾病诊断后生成病症图解、治疗方法示意图
- 交互方式：类似 nano banana 科普博客，文字 + 图片并茂
- 集成到 Skills：疾病预测、巡检报告等需要可视化科普的场景

#### 任务清单

| 任务 | 负责人 | 工作量 | 时间安排 | 依赖 | 状态 |
|------|--------|--------|----------|------|------|
| **A12: 生图模型集成** ⭐新增 | A | 2天 | Week 5 第 1-2 天 | A10 | 待开始 |
| - 配置 qwen-image-2.0 / qwen-image-2.0-pro API | | | | | |
| - 实现 `src/agents/tools/image_generation_tool.py` | | | | | |
| - 创建 `src/agents/skills/configs/image_gen.yaml` 技能配置 | | | | | |
| - 测试生图质量和响应时间 | | | | | |
| **A13: 图文科普 Skills 设计** ⭐新增 | A + D | 2天 | Week 5 第 2-3 天 | A12 | 待开始 |
| - 设计疾病预测图文科普流程（诊断 → 生图 → 图解） | | | | | |
| - 设计巡检报告图文展示（问题 → 示意图 → 解决方案） | | | | | |
| - 实现多模态 + 生图协同逻辑 | | | | | |
| **D6: 图文科普前端展示** ⭐新增 | D | 1天 | Week 5 第 3 天 | A13 | 待开始 |
| - 图文科普结果展示组件 | | | | | |
| - 图片生成进度动画 | | | | | |
| - 图片下载/分享功能 | | | | | |
| **B4: 前端功能入口设计** | B | 2天 | Week 6 第 1-2 天 | - | 待开始 |
| - 设计外部服务入口卡片 UI | | | | | |
| - 在主页面欢迎区域集成服务入口 | | | | | |
| - 添加服务可用性检测/状态显示 | | | | | |
| **A3: 外部服务配置管理** | A | 1天 | Week 5 任意时间 | - | 待开始 |
| - 创建 `frontend/src/config/external-services.ts` | | | | | |
| - 支持环境变量配置 URL（开发/生产） | | | | | |
| - 后端 `src/config/external_services.py` 配置同步 | | | | | |
| **A4: 外部服务健康检查** | A | 1天 | Week 6 第 1 天 | A3 | 待开始 |
| - 实现 `/health/external-services` API | | | | | |
| - 定期检查外部服务可用性 | | | | | |
| - 前端状态指示灯 | | | | | |
| **A5: 端到端测试用例** | A | 1天 | Week 6 第 3 天 | 阶段二 | 待开始 |
| - 编写端到端测试脚本 | | | | | |
| - 覆盖主要功能场景（含图文科普） | | | | | |
| **D5: TTS 语音输出** | D | 2天 | Week 6 任意时间（独立任务） | - | 待开始 |
| - 集成 Web Speech API | | | | | |
| - 添加语音播报按钮和开关 | | | | | |
| - 支持长文本分段播报 + 进度显示 | | | | | |

**⚠️ Week 5-6 任务执行顺序**：
1. **Week 5 第 1 天**：A12（生图模型配置）启动
2. **Week 5 第 2 天**：A12 继续 + A13（图文科普设计）启动
3. **Week 5 第 3 天**：A13 继续 + D6（图文科普前端）+ A3（外部服务配置）
4. **Week 6 第 1 天**：A3/A4（配置支持）+ B4 启动
5. **Week 6 第 2 天**：B4 继续 + D5 启动
6. **Week 6 第 3 天**：A5（端到端测试）+ B4 收尾
7. **Week 6 第 4-5 天**：切换到阶段四（C3/C4 部署预演）

#### 里程碑
- [ ] 外部服务入口 UI 上线
- [ ] 外部服务健康检查上线
- [ ] TTS 语音播报功能上线
- [ ] 环境配置支持外部服务 URL
- [ ] 端到端测试覆盖完成
- [ ] ⭐新增：生图模型集成完成（qwen-image-2.0）
- [ ] ⭐新增：图文科普 Skills 上线（疾病预测、巡检报告）
- [ ] ⭐新增：图文科普前端展示组件上线

---

### 阶段四：部署上线（Week 6 第4-5天 + Week 7）

#### 目标
完成生产环境配置和部署验证。

#### ⚠️ Week 6 时间分配（重要）

| 时间 | 阶段 | 负责人 | 任务 |
|------|------|--------|------|
| **Week 6 第 1-3 天** | 阶段三 | B, A | 外部服务入口开发（B4、A3、A4、A5） |
| **Week 6 第 4-5 天** | 阶段四 | C + A | 生产环境配置 + 部署预演（C3、C4） |

**并行策略**：
- Week 6 前 3 天：B 和 A 并行开发外部服务入口
- Week 6 后 2 天：C 启动生产环境配置，A 参与部署预演
- 避免 B 和 C 的任务冲突（B 做前端，C 做后端配置）

#### 重要说明
**降低部署风险**：将部署任务拆分到 Week 6-7，避免最后一周高压工作。

#### 任务清单

| 任务 | 负责人 | 工作量 | 时间安排 | 依赖 | 状态 |
|------|--------|--------|----------|------|------|
| **C3: 生产环境配置** | C | 2天 | Week 6 第 4 天 + Week 7 第 1 天 | 所有功能 | 待开始 |
| - 配置 `.env.production` | | | | | |
| - 优化 Docker 镜像 | | | | | |
| - 配置外部服务 URL | | | | | |
| **C4: 部署预演** | C + A | 1天 | Week 6 第 5 天 | C3（部分配置完成后） | 待开始 |
| - 在测试环境进行完整部署演练 | | | | | |
| - 验证部署流程 | | | | | |
| - 记录问题和解决方案 | | | | | |
| **A6: 外部服务协调** | A | 2天 | Week 7 | - | 待开始 |
| - 与外部团队确认部署地址 | | | | | |
| - 配置生产环境外部服务 URL | | | | | |
| - 服务间连通性测试 | | | | | |
| - 灰度发布方案设计 | | | | | |
| **C5: 部署验证测试** | C + B | 2天 | Week 7 | C4 | 待开始 |
| - 完整测试套件执行 | | | | | |
| - 压力测试（并发用户） | | | | | |
| - 稳定性测试（长时间运行） | | | | | |
| - 外部服务跳转验证 | | | | | |
| **C6: 监控运维方案** | C | 1天 | Week 7 | 部署完成 | 待开始 |
| - 健康检查端点完善 | | | | | |
| - 日志轮转配置 | | | | | |
| - 回滚方案文档 | | | | | |

#### 里程碑
- [ ] Week 6: 生产环境配置完成
- [ ] Week 6: 部署预演通过
- [ ] Week 7: 外部服务 URL 配置完成
- [ ] Week 7: 部署验证通过（含外部服务跳转）
- [ ] Week 7: v0.1 版本发布

---

## 五、技术实现细节

### 5.1 多模态模型集成（qwen3.5-plus）

**配置文件**: `src/config.py` - 添加 qwen-vl 模型配置

**关键修改**:
- `src/agents/utils.py`: 添加多模态模型获取方法
- `src/agents/orchestrator_agent_v2.py`: 增强多模态提示词

#### ✅ 已完成：前端多模态消息封装（2026-03-19）

**问题已解决**：
- 前端现在正确传递图片 base64 数据
- 后端构建 OpenAI 兼容的多模态消息格式
- LLM 正确接收图像数据进行多模态理解

**实现方案**：
```python
HumanMessage(content=[
    {"type": "text", "text": "用户问题"},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
])
```

### 5.2 网络搜索功能

**技术选型**: Tavily API（LangChain 官方推荐）

**新文件**:
- `src/agents/tools/web_search_tool.py` - 搜索工具实现
- `src/agents/skills/configs/web_search.yaml` - 搜索技能配置

### 5.3 定价工具集成搜索

**修改文件**: `src/agents/tools/pricing_tool.py`

**实现逻辑**:
```python
# pricing_tool.py 新增
async def analyze_with_real_time_price(product: str, enable_search: bool = True):
    base_analysis = analyze_from_knowledge_base(product)
    if enable_search:
        market_price = await web_search_tool.search(f"{product} 市场价格")
        return merge_and_compare(base_analysis, market_price)
    return base_analysis
```

### 5.4 检测多模态增强

**修改文件**: `src/agents/tools/detection_tools.py`

**实现逻辑**:
```python
# 检测结果后处理
detection_result = detect(image)
vl_explanation = await qwen_vl_model.generate([
    {"type": "image", "image": image},
    {"type": "text", "text": f"检测结果：{detection_result}。请解释并提供处理建议。"}
])
return {
    "detection": detection_result,
    "explanation": vl_explanation,
    "suggestions": extract_suggestions(vl_explanation)
}
```

### 5.5 巡检图片分析增强

**修改文件**: `src/agents/tools/farm_inspection_tool.py`

**实现逻辑**:
```python
# 支持多图片输入
async def analyze_inspection_images(images: List[Image]):
    prompts = [
        [{"type": "image", "image": img}, {"type": "text", "text": "分析这张巡检照片"}]
        for img in images
    ]
    results = await qwen_vl_model.batch_generate(prompts)
    return synthesize_inspection_report(results)
```

### 5.6 疾病预测多模态

**修改文件**: `src/agents/tools/disease_prediction_tool.py`

**实现逻辑**:
```python
# 支持图片 + 症状文本
async def predict_disease(image: Image, symptoms: str):
    image_analysis = await qwen_vl_model.analyze(image)
    combined_input = f"""
    图片分析：{image_analysis}
    症状描述：{symptoms}
    综合判断可能的疾病及建议。
    """
    return await disease_model.predict(combined_input)
```

### 5.7 外部功能入口集成

**前端配置**: `frontend/src/config/external-services.ts` - 定义三个外部服务的名称、图标、描述和 URL

**后端配置**: `src/config/external_services.py` - 同步外部服务 URL 配置

**UI 集成**: 在 `frontend/src/app/page.tsx` 欢迎区域添加服务入口卡片

**环境变量**:
```bash
NEXT_PUBLIC_MANAGEMENT_URL=http://localhost:3002
NEXT_PUBLIC_PLANNING_URL=http://localhost:3003
NEXT_PUBLIC_LEGAL_URL=http://localhost:3004
```

### 5.8 外部服务健康检查

**新增 API**: `service/api/health.py`

**实现逻辑**:
```python
@router.get("/health/external-services")
async def check_external_services():
    results = {}
    for service in EXTERNAL_SERVICES:
        results[service.name] = await check_service_availability(service.url)
    return {"status": "healthy", "services": results}
```

### 5.9 Qwen3.6 模型适配 ⭐新增

**参考文档**: https://qwen.ai/blog?id=qwen3.6

**配置文件**: `src/config.py` - 添加 qwen3.6 模型配置

**关键特性**:
- 能力增强：更强的推理能力、更好的多语言支持
- 多模态能力提升：更准确的图像理解
- 建议优先用于复杂推理任务

**配置示例**:
```python
# src/config.py
QWEN_MODELS = {
    "qwen3.6": {
        "model_name": "qwen3.6",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "capabilities": ["text", "vision", "reasoning"],
        "recommended_for": ["complex_analysis", "multi_step_reasoning"]
    }
}
```

### 5.10 模型分级选择机制 ⭐新增

**核心思想**: 根据任务复杂度自动选择合适的模型，降低 API 成本

**实现文件**: `src/agents/utils/model_selector.py`

**分级规则**:
| 任务类型 | 推荐模型 | 理由 |
|----------|----------|------|
| 复杂推理（疾病诊断、定价分析） | qwen3.6 / qwen3.5-plus | 需要强推理能力 |
| 固定工作流（检测触发、简单问答） | qwen3.5-flash | 速度快、成本低 |
| 多模态分析（图片理解） | qwen3.5-plus / qwen3.5-flash | 两者都支持多模态 |
| 生图任务 | qwen-image-2.0 | 专用生图模型 |

**实现逻辑**:
```python
# src/agents/utils/model_selector.py
class ModelSelector:
    def select_model(self, task_type: str, complexity: str) -> str:
        if task_type in ["disease_prediction", "pricing_analysis"]:
            return "qwen3.6"  # 复杂推理
        elif task_type in ["detection_trigger", "simple_query"]:
            return "qwen3.5-flash"  # 简单任务
        elif task_type == "image_generation":
            return "qwen-image-2.0"
        return "qwen3.5-plus"  # 默认
```

**Skill 级别配置**:
```yaml
# src/agents/skills/configs/disease_prediction.yaml
model_preference:
  primary: qwen3.6
  fallback: qwen3.5-plus
  
# src/agents/skills/configs/detection.yaml
model_preference:
  primary: qwen3.5-flash  # 检测触发用 flash 即可
```

### 5.11 前端 Demo 卡片完善 ⭐新增

**目标**: 为每个 Skill 创建预设 Demo 示例，用户点击即可触发

**前端配置**: `frontend/src/config/demo-cards.ts`

**Demo 卡片设计**:
```typescript
// frontend/src/config/demo-cards.ts
export const DEMO_CARDS = [
  {
    skill: "pest_detection",
    title: "病虫害识别",
    icon: "🔍",
    demo_input: {
      text: "请帮我识别这张图片中的病虫害",
      image: "/demo_images/pest_sample.jpg"
    }
  },
  {
    skill: "disease_prediction",
    title: "疾病预测",
    icon: "🏥",
    demo_input: {
      text: "我的奶牛最近食欲不振，体温升高，请帮我分析可能的疾病",
      image: "/demo_images/cow_symptom.jpg"
    }
  },
  {
    skill: "pricing_analysis",
    title: "定价分析",
    icon: "💰",
    demo_input: {
      text: "请分析当前大米的市场定价因素"
    }
  },
  // ... 其他 Skill Demo
]
```

**一键触发逻辑**:
```typescript
// frontend/src/app/page.tsx
const handleDemoClick = (demo: DemoCard) => {
  setInputText(demo.demo_input.text)
  if (demo.demo_input.image) {
    // 自动加载 Demo 图片
    setImagePreview(demo.demo_input.image)
  }
  // 自动触发对话
  handleSendMessage()
}
```

### 5.12 生图模型集成 ⭐新增

**模型**: qwen-image-2.0 / qwen-image-2.0-pro

**配置文件**: `src/config.py` - 添加生图模型配置

**实现文件**: `src/agents/tools/image_generation_tool.py`

**核心能力**:
- 文生图：根据文字描述生成图片
- 图解科普：生成病症示意图、治疗方法图解
- 交互增强：文字回答 + 配图，类似 nano banana 科普博客

**工具实现**:
```python
# src/agents/tools/image_generation_tool.py
from langchain.tools import BaseTool

class ImageGenerationTool(BaseTool):
    name = "image_generation"
    description = "生成图解科普图片，用于病症说明、治疗方法展示"
    
    async def _arun(self, prompt: str, style: str = "illustration") -> str:
        # 调用 qwen-image-2.0 API
        response = await dashscope_image_api.generate(
            model="qwen-image-2.0",
            prompt=prompt,
            style=style
        )
        return response.image_url
```

### 5.13 图文科普 Skills 设计 ⭐新增

**典型应用场景**:

**疾病预测图文科普**:
```
用户上传图片 + 症状描述
    ↓
Qwen-VL 分析图片 + Qwen 推理病症
    ↓
调用 image_generation_tool 生成病症图解
    ↓
输出：文字诊断 + 症状图解 + 治疗建议 + 治疗示意图
```

**巡检报告图文展示**:
```
用户上传巡检照片
    ↓
Qwen-VL 分析问题（如设备故障）
    ↓
调用 image_generation_tool 生成问题示意图
    ↓
输出：文字报告 + 问题标注图 + 解决方案图解
```

**Skill 配置示例**:
```yaml
# src/agents/skills/configs/disease_prediction.yaml
name: disease_prediction
tools:
  - disease_prediction_tool
  - image_generation_tool  # 新增生图工具
workflow:
  - step: analyze_symptoms
    model: qwen3.6
  - step: generate_explanation_image
    tool: image_generation_tool
    prompt_template: "生成 {disease_name} 症状示意图，展示 {key_symptoms}"
```

---

## 六、关键风险与缓解

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| Qwen-VL API 配额不足 | 高 | 提前申请企业配额，准备降级方案 |
| Tavily 搜索不稳定 | 中 | 实现搜索结果缓存，多搜索源备份 |
| Docker 镜像体积过大 | 中 | 使用 ONNX 量化，多阶段构建 |
| 移动端性能问题 | 低 | 代码分割，懒加载优化 |
| Qwen-VL 多模态输入兼容性 | 中 | 提前测试不同图片格式和尺寸，实现格式转换 |
| 外部服务地址变更 | 中 | 使用配置文件，支持运行时更新，健康检查监控 |
| TTS 长文本播报卡顿 | 低 | 分段播报 + 进度显示 + 可暂停控制 |
| 定价搜索结果质量 | 中 | 实现 result_filter 策略，过滤无效结果，置信度评分 |
| 部署时间窗口不足 | 高 | 提前到 Week 6 开始部署准备，部署预演 |
| ⭐新增：生图模型 API 成本过高 | 中 | 使用 qwen-image-2.0（非 pro），限制生图调用频率，仅在关键场景使用 |
| ⭐新增：模型分级判断不准确 | 中 | 设计明确的任务分类规则，人工审核分级效果，逐步优化规则 |
| ⭐新增：Demo 卡片图片加载慢 | 低 | 使用本地 Demo 图片，预加载优化，压缩图片体积 |
| ⭐新增：Qwen3.6 API 兼容性问题 | 中 | 测试 API 接口兼容性，准备降级到 Qwen3.5-plus |
| ⭐新增：图文科普生成时间过长 | 中 | 异步生图，文字先返回，图片后续推送，进度提示 |

---

## 七、外部依赖清单

### API 密钥
- [ ] qwen3.5-plus API Key（阿里云 DashScope）
- [ ] qwen3.5-flash API Key（阿里云 DashScope）⭐新增
- [ ] qwen3.6 API Key（阿里云 DashScope）⭐新增
- [ ] qwen-image-2.0 API Key（阿里云 DashScope）⭐新增
- [ ] Tavily Search API Key

### 外部服务部署
- [ ] 乡村经营服务部署地址
- [ ] 规划方案服务部署地址
- [ ] 法律助手服务部署地址

---

## 八、测试策略

### 测试层级
1. **单元测试**: 工具函数、RAG 检索
2. **集成测试**: 端到端对话流程
3. **性能测试**: 并发用户、响应时间
4. **用户验收**: 真实场景、专家评审

### 测试命令
```bash
# 快速测试
bash scripts/dev/check.sh --test fast

# 完整测试
bash scripts/dev/check.sh --test full

# 生产环境测试
bash scripts/dev/test_production.sh
```

---

## 八、成员工作量矩阵

| 成员 | Week 1-2 | Week 3-4 | Week 5-6 | Week 7 | 合计 | 专长利用率 |
|------|----------|----------|----------|--------|------|------------|
| **A** | A1(3) + A2(3) = 6天 | A7(1) + A8(2) + A9(1) + A10(1) + A11(2) = 7天 | A3(1) + A4(1) + A5(1) + A12(2) + A13(1) = 6天<br>**Week 6 第 4-5 天：参与 C4 部署预演** | A6(2) = 2天 | **21天** | ⭐⭐⭐ |
| **B** | B1(2) = 2天 | B2(3) + B3(1) + B5(2) = 6天 | B4(2) = 2天<br>**Week 6 第 1-3 天：前端入口开发** | - | **10天** | ⭐⭐⭐ |
| **C** | C1(2) + C2(2) = 4天 | - | C3(2) + C4(1) = 3天<br>**Week 6 第 4-5 天：生产配置 + 预演** | C5(2) + C6(1) = 3天 | **10天** | ⭐⭐⭐ |
| **D** | D1(2) + D2(2) = 4天 | D3(2) + D4(3) = 5天 | D5(2) + D6(1) + A13协作(1) = 4天 | - | **13天** | ⭐⭐⭐ |

**⚠️ Week 5-6 任务并行说明**：
- **Week 5**：A（生图模型 + 图文科普设计）+ D（图文科普前端 + 协作设计）并行
- **Week 6 前 3 天**：B（前端入口）+ A（配置支持）+ D（TTS）并行
- **Week 6 后 2 天**：C（生产配置）+ A（部署预演协助）并行
- **D5（TTS）**：可在 Week 6 任意时间独立完成，不阻塞其他任务

**对比 v2.3 优化**：
- **A**: 15天 → 21天（+6）⭐新增：Qwen3.6适配 + 模型分级 + 生图模型
- **B**: 8天 → 10天（+2）⭐新增：前端 Demo 卡片完善
- **C**: 10天 → 10天（不变）
- **D**: 11天 → 13天（+2）⭐新增：图文科普前端展示

**工作量平衡**：
- A 工作量最高（21天），负责核心架构升级（Qwen3.6、模型分级、生图）
- 所有成员工作量在 10-21 天之间
- 每位成员的专长都得到充分利用
- Week 7 不再是 C 的高压周（3天 vs 原 5天）

---

## 九、关键文件索引

| 文件 | 作用 | 负责人 |
|------|------|--------|
| `src/config.py` | 模型配置（含 Qwen3.6、flash、生图） | A |
| `src/agents/orchestrator_agent_v2.py` | Agent 主入口 | A |
| `src/agents/utils/model_selector.py` | ⭐新增：模型分级选择器 | A |
| `src/agents/tools/web_search_tool.py` | 搜索工具 | A |
| `src/agents/skills/configs/web_search.yaml` | 搜索技能 | A |
| `src/agents/tools/image_generation_tool.py` | ⭐新增：生图工具 | A |
| `src/agents/skills/configs/image_gen.yaml` | ⭐新增：生图技能配置 | A |
| `src/agents/tools/pricing_tool.py` | 定价工具（集成搜索） | C |
| `src/agents/tools/detection_tools.py` | 检测工具（多模态增强） | C |
| `src/agents/tools/farm_inspection_tool.py` | 巡检工具（多图片 + 图文科普） | D |
| `src/agents/tools/disease_prediction_tool.py` | 疾病预测（多模态 + 图文科普） | D |
| `src/agents/skills/configs/planning.yaml` | 规划技能 | B |
| `src/config/external_services.py` | 外部服务 URL 配置 | A |
| `service/api/health.py` | 外部服务健康检查 | A |
| `frontend/src/config/external-services.ts` | 外部服务前端配置 | A |
| `frontend/src/config/demo-cards.ts` | ⭐新增：Demo 卡片配置 | B |
| `frontend/src/app/page.tsx` | 主页面（含服务入口 + Demo 卡片） | B |
| `frontend/src/components/ImageExplanation.tsx` | ⭐新增：图文科普展示组件 | D |
| `.env.production` | 生产配置（含外部服务 URL） | C |
| `docker-compose.yml` | 部署编排 | C |
| `docs/guides/qwen-vl-advanced.md` | Qwen-VL 技术预研报告 | A |
| `docs/guides/model-selection.md` | ⭐新增：模型分级选择指南 | A |
| `docs/guides/image-generation.md` | ⭐新增：生图模型使用指南 | A |
| `docs/guides/performance-optimization.md` | 性能优化文档 | A |
| `docs/guides/development.md` | 开发工作流（含故障排查） | A |

---

## 十、版本规划

| 版本 | 日期 | 主要内容 | 里程碑 |
|------|------|----------|--------|
| v0.1-alpha | Week 2 | 多模态 + 搜索功能 | - Agent 支持多模态输入<br>- Agent 可以联网搜索<br>- RAG 系统支持混合检索<br>- 定价工具支持实时价格查询 |
| v0.1-beta | Week 4 | UI 优化 + 模型升级 | - 差异化 UI 设计完成<br>- 移动端适配完成<br>- 工具调用可视化上线<br>- 知识溯源功能上线<br>- RAG 混合检索策略优化完成<br>- ⭐新增：Qwen3.6 模型适配完成<br>- ⭐新增：模型分级选择机制上线<br>- ⭐新增：前端 Demo 卡片一键触发上线 |
| v0.1-rc | Week 6 | 外部服务 + 生图 + TTS | - **Week 5**：生图模型集成完成<br>- **Week 5**：图文科普 Skills 上线<br>- **Week 5**：图文科普前端展示上线<br>- **Week 6 第 1-3 天**：外部服务入口 UI 上线<br>- **Week 6 第 1-3 天**：外部服务健康检查上线<br>- **Week 6 第 1-3 天**：TTS 语音播报功能上线<br>- **Week 6 第 1-3 天**：端到端测试覆盖完成<br>- **Week 6 第 4-5 天**：生产环境配置完成<br>- **Week 6 第 4-5 天**：部署预演通过 |
| v0.1 | Week 7 | 正式发布 | - 外部服务 URL 配置完成<br>- 部署验证通过<br>- 监控运维方案就绪<br>- v0.1 版本发布 |

---

## 十一、版本优化总结

### v2.4 主要改进（2026-04-03）⭐新增

1. **新增四大需求**：
   - 前端 Demo 卡片完善（B5）- 各功能一键触发
   - 模型分级选择机制（A11）- plus/flash 自动切换，降低成本
   - 生图模型集成（A12）- qwen-image-2.0 图文科普
   - Qwen3.6 适配（A10）- 升级到更强模型

2. **工作量调整**：
   - A: 15天 → 21天（+6）- 承担核心架构升级
   - B: 8天 → 10天（+2）- 前端 Demo 卡片
   - D: 11天 → 13天（+2）- 图文科普前端展示

3. **新增技术实现章节**（5.9 - 5.13）：
   - Qwen3.6 模型适配方案
   - 模型分级选择机制设计
   - 前端 Demo 卡片配置
   - 生图模型集成方案
   - 图文科普 Skills 设计

4. **新增风险项**：
   - 生图模型 API 成本控制
   - 模型分级判断准确性
   - Demo 卡片图片加载优化
   - 图文科普生成时间控制

### v2.0-v2.3 主要改进

1. **工作量重新分配**：所有成员工作量在 8-15 天之间，分配均衡
2. **充分利用成员专长**：
   - 成员 C 的检测/定价专长得到利用（C1、C2 任务）
   - 成员 D 的巡检/疾病预测专长得到利用（D1、D2 任务）
3. **降低部署风险**：将部署任务分散到 Week 6-7，避免最后一周高压
4. **明确 UX 目标**：增加了与通用 AI 差异化的具体体现和验收标准
5. **新增关键功能**：
   - 定价工具集成网络搜索
   - 检测服务多模态增强
   - 巡检多图片分析
   - 疾病预测多模态输入
   - 外部服务健康检查
   - 端到端测试用例
   - Qwen-VL 技术预研
   - 工具性能优化
   - 完善文档体系
6. **完善风险清单**：补充了新增风险和缓解策略

### 新增任务汇总

| 任务编号 | 任务名称 | 负责人 | 工作量 | 阶段 |
|----------|----------|--------|--------|------|
| C1 | 定价工具集成搜索 | C | 2天 | Week 1-2 |
| C2 | 检测多模态增强 | C | 2天 | Week 1-2 |
| D1 | 巡检图片分析增强 | D | 2天 | Week 1-2 |
| D2 | 疾病预测多模态 | D | 2天 | Week 1-2 |
| B3 | RAG 与搜索融合测试 | B | 1天 | Week 3-4 |
| A7 | Qwen-VL 技术预研 | A | 1天 | Week 3-4 |
| A8 | 工具性能优化 | A | 2天 | Week 3-4 |
| A9 | 文档完善 | A | 1天 | Week 3-4 |
| A4 | 外部服务健康检查 | A | 1天 | Week 5-6 |
| A5 | 端到端测试用例 | A | 1天 | Week 5-6 |
| **⭐A10** | **Qwen3.6 模型适配** | **A** | **1天** | **Week 3-4** |
| **⭐A11** | **模型分级选择机制** | **A** | **2天** | **Week 3-4** |
| **⭐B5** | **前端 Demo 卡片完善** | **B** | **2天** | **Week 3-4** |
| **⭐A12** | **生图模型集成** | **A** | **2天** | **Week 5** |
| **⭐A13** | **图文科普 Skills 设计** | **A + D** | **2天** | **Week 5** |
| **⭐D6** | **图文科普前端展示** | **D** | **1天** | **Week 5** |

### 文件变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.2 → v2.0 | 2026-03-13 | 优化工作量分配，充分利用成员专长，降低部署风险 |
| v2.0 → v2.1 | 2026-03-13 | 新增成员 A Week 3-4 任务（A7/A8/A9） |
| v2.1 → v2.2 | 2026-03-19 | 新增多模态消息封装待办任务（5.1 章节） |
| v2.3 → v2.4 | 2026-04-03 | ⭐新增四大需求：前端 Demo 卡片、模型分级选择、生图模型集成、Qwen3.6 适配 |
| — | 2026-04-05 | 🔄 状态同步：更新成员 B 任务完成状态（B1✅、B2✅、B5✅） |
| — | 2026-04-05 | ✅ B3 完成：混合检索 A/B 测试，推荐 `bm25_dominant` 配置（关键词覆盖率 97%） |
| — | 2026-04-05 | 🧹 代码清理：删除过时测试文件，修复导入路径，清理重复导入 |
| — | 2026-04-06 | 📚 知识库补充：完成15个典型案例入库目标，切片796个，覆盖五大振兴 |

---

## 十二、知识库补充计划

### 当前知识库状态（更新：2026-04-06）

```
src/data/
├── policies/           # 政策文件（3个有效）
│   ├── 2026中央一号文件-农业农村现代化乡村全面振兴.md
│   ├── 乡村全面振兴规划2024-2027.md
│   └── 农业农业农村部2026年实施意见.md
│
├── cases/              # 案例文件（已补充 7 个 Markdown）
│   ├── 产业振兴/
│   │   ├── 广西贵港港北区-科技种粮案例.md          ✅
│   │   ├── 东山县城乡融合发展实践.md               ✅
│   │   ├── 辽宁台安县-绿色低碳农业产业链案例.md     ✅ 2026-04-06 新增
│   │   └── 湖北十堰市-库区农业绿色发展案例.md       ✅ 2026-04-06 新增
│   ├── 人才振兴/
│   │   └── 浙江宁波-AI新农具数字人IP案例.md         ✅
│   ├── 文化振兴/
│   │   └── 天津宁河后江石沽村-全国文明村镇案例.md   ✅
│   ├── 生态振兴/
│   │   ├── 贵州遵义-四在农家和美乡村案例.md         ✅ 2026-04-06 新增
│   │   ├── 辽宁台安县-绿色低碳农业产业链案例.md     ✅ 2026-04-06 新增
│   │   └── 湖北十堰市-库区农业绿色发展案例.md       ✅ 2026-04-06 新增
│   ├── 组织振兴/
│   │   └── 贵州遵义-四在农家和美乡村案例.md         ✅ 2026-04-06 新增
│   └── 罗浮—长宁山镇融合发展规划.pptx              （原有）
│
└── README.md
```

### 补充进度

| 类型 | 目标数量 | 已完成 | 待补充 | 状态 |
|------|----------|--------|--------|------|
| **产业振兴案例** | 3-5 个 | 5 个 | 0 个 | ✅ 已完成 |
| **人才振兴案例** | 1-2 个 | 1 个 | 0-1 个 | ✅ 基本完成 |
| **文化振兴案例** | 1-2 个 | 1 个 | 0-1 个 | ✅ 基本完成 |
| **生态振兴案例** | 1-2 个 | 3 个 | 0 个 | ✅ 已完成 |
| **组织振兴案例** | 1-2 个 | 3 个 | 0 个 | ✅ 已完成 |
| **省级/市县政策** | 5-10 个 | 0 个 | 5-10 个 | ❌ 待开始 |

### 已补充案例详情

| 案例 | 类型 | 来源 | 数据量化 | 可复制性 |
|------|------|------|----------|----------|
| 广西贵港港北区（科技种粮） | 产业振兴 | 农业农村部官网 | ✅ 充足 | ✅ 高 |
| 东山县城乡融合发展实践 | 产业振兴 | 农业农村部官网 | ✅ 充足 | ✅ 高 |
| 辽宁台安县（绿色低碳农业产业链） | 产业振兴+生态振兴 | 农业农村部官网 | ✅ 充足（160亿产值） | ✅ 高 |
| 湖北十堰市（库区农业绿色发展） | 生态振兴+产业振兴 | 农业农村部官网 | ✅ 充足（558亿旅游收入） | ✅ 高 |
| **新疆伊吾县（边疆民族地区乡村振兴示范村）** | **组织振兴+产业振兴** | **农业农村部官网** | **✅ 充足（2.5亿销售额）** | **✅ 高** |
| **云南楚雄州（西部高原乡村振兴）** | **组织振兴+产业振兴** | **农业农村部官网** | **✅ 充足（75.5亿资金）** | **✅ 高** |
| **湖南祁阳市（片区化乡村振兴）** | **产业振兴+组织振兴** | **农业农村部官网** | **✅ 充足（200亿产值）** | **✅ 高** |
| **浙江绍兴市（和美越乡共富片区）** | **产业振兴+组织振兴** | **农业农村部官网** | **✅ 充足（165万村均收入）** | **✅ 高** |
| **山西省（千村示范万村提升）** | **组织振兴+产业振兴** | **农业农村部官网** | **✅ 充足（100亿省级资金）** | **✅ 高** |
| **江苏南京溧水区（三多合一改革）** | **组织振兴+产业振兴** | **农业农村部官网** | **✅ 充足（30亿整合资金）** | **✅ 高** |
| **福建省（山海协作城乡融合）** | **人才振兴+产业振兴+组织振兴** | **农业农村部官网** | **✅ 充足（1.8万亿涉农贷款）** | **✅ 高** |
| **上海市（沪派江南三园工程）** | **文化振兴+产业振兴+生态振兴+组织振兴** | **农业农村部官网** | **✅ 充足（164个示范村）** | **✅ 高** |
| 天津宁河后江石沽村（文明村镇） | 文化振兴 | 农业农村部官网 | ⚠️ 中等 | ⚠️ 中等 |
| 浙江宁波（AI数字人IP） | 人才振兴 | 农业农村部官网 | ✅ 充足 | ✅ 高 |
| 贵州遵义（四在农家·和美乡村） | 生态振兴+组织振兴 | 农业农村部官网 | ✅ 充足（1728村） | ✅ 高 |

### 缺失内容分析

| 优先级 | 缺失类型 | 影响 | 数量建议 | 当前状态 |
|--------|----------|------|----------|----------|
| **P1 高** | 五大振兴案例库 | 无法提供振兴案例 | 10-15 个 | ✅ 已完成 **15/15** |
| **P1 高** | 省级/市县政策 | 缺少地方细节 | 5-10 个 | ❌ 未开始 |
| **P2 中** | 失败案例/风险警示 | 无法提供风险预警 | 3-5 个 | ❌ 未开始 |
| **P2 中** | 实施方案模板 | 无法提供可复制方案 | 3-5 个 | ❌ 未开始 |
| **P3 低** | 技术规范/法律法规 | 缺少标准参考 | 按需补充 | ❌ 未开始 |

### 推荐补充目录结构

```
src/data/
├── policies/
│   ├── 国家级/              # 现有文件移入
│   ├── 省级/
│   │   ├── 广东省乡村振兴政策汇编.md
│   │   └── 浙江省乡村振兴政策汇编.md
│   └── 市县/
│       └── 博罗县乡村振兴实施方案.md
│
└── cases/
    ├── 产业振兴/
    │   ├── 浙江安吉-乡村旅游发展案例.md
    │   ├── 山东寿光-蔬菜产业案例.md
    │   └── 四川蒲江-柑橘产业链案例.md
    ├── 人才振兴/
    │   └── 新型职业农民培育案例.md
    ├── 文化振兴/
    │   └── 乡村文化传承案例.md
    ├── 生态振兴/
    │   └── 农村人居环境整治案例.md
    └── 组织振兴/
        └── 村集体经济发展案例.md
```

### 文档格式要求

- **格式**：Markdown（推荐）
- **结构**：背景 → 方案 → 效果 → 经验总结
- **切片**：按标题层级自动分割
