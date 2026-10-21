# 唤醒词难度实验工程

本工程把现有六个原始 ASR 分数作为初筛证据，并提供可落地的唤醒词采集、验证和换词流程。分数定义、样本量和正负样本构成未知，所以不能从单次分数虚构置信区间或宣布显著性。配套脚本从实际系统导出的分数中，在开发集选择阈值，并在独立测试集评估。

## 当前实测排序

| 短语 | 当前分数 | 比 hey google 低 |
|---|---:|---:|
| hey google | 0.936 | — |
| hey tesla | 0.895 | 0.041 |
| hey siri | 0.865 | 0.071 |
| hey eva | 0.756 | 0.180 |
| hey even | 0.553 | 0.383 |
| hey ixio | 0.331 | 0.605 |

在测试协议一致、分数等于准确率且样本量相同的前提下，排序为 Google > Tesla > Siri > Eva > Even > Ixio。Eva、Even、Ixio 分别落后 Google 18.0、38.3、60.5 个百分点。若分数真是准确率，它们的错误率约为 Google 的 3.8、7.0、10.5 倍；该推算不适用于模型置信度或其他定义的分数。缺少分母和测试构成时，当前只能称为初筛排序。

## 六个词的发音风险假设

所有发音是假设，须用目标用户录音验证。hey 前缀相同，有助于控制测试条件，但 hey 与目标词之间的连读边界本身也可能造成错误。

| 短语 | 典型读音结构 | 当前分数下的风险解释与要验证的点 |
|---|---|---|
| hey google | /heɪ ˈɡuːɡəl/ | 当前基线最高。Google 高频，通用 ASR 的词频/语言模型可能帮助转写，不能把优势全归于声学可分性。固定解码、上下文和词表设置。 |
| hey tesla | /heɪ ˈtɛslə/ | 0.895 接近高分组。/sl/ 辅音群可能在快语速和口音下弱化；重点检查 /s/ 丢失、噪声及日常提及 Tesla 的负例。 |
| hey siri | /heɪ ˈsɪri/ | 0.865。词较短，尾部近音 /r/ 的实现可能随口音改变；检查不同口音、快语速和近似姓名/命令误触发。 |
| hey eva | /heɪ ˈiːvə/、/heɪ ˈɛvə/ 等 | 0.756，先诊断再决定是否放弃。Eva 以元音开头，hey 的 /eɪ/ 与首元音可能连读或合并；Eva 本身读法也可能变化。与 Even 共用可能的 /iːv/ 起始，尾部 /ə/ 与 /ən/ 易被截断/噪声影响。标注 FN 在词边界、首元音还是尾部。 |
| hey even | /heɪ ˈiːvən/ | 0.553，高风险。可能与 Eva 开头近似，尾部 /n/ 是关键区分线索；Even 是常见词，ASR 语言先验可能偏好它，但不等于唤醒检测可靠。重点计算 Eva/Even 成对混淆率和尾 /n/ 漏检。 |
| hey ixio | 尚无唯一自然读法，可能 /ɪk.si.oʊ/、/ɪk.sɪ.oʊ/ 等 | 0.331，当前最弱且最应先检查“读法是否统一”。不同说话人的音节数/元音若不一致，就不是同一稳定目标；罕见拼写也可能被 BPE 拆成低频子词，这是待测假设。先做不看示范的盲读，再规范读音复测，分离发音方差、tokenizer 与声学错误。 |

### 初步判断

hey eva 是可修复性未知的中高风险项，不能只凭 0.756 判定淘汰；若低分集中于 Eva 变体或 hey/Eva 边界，补充对应样本后应复测。hey even 的低分需要检查尾音和 Eva/Even 混淆。hey ixio 既分数最低又读法不明确，如果目标用户无法稳定统一读法，建议优先从候选池淘汰。所有三者都必须测负例误触发，ASR 正确转写率不能替代 FAR/小时。

## 实验设计

### A. 固定任务与记录项

1. 记录 checkpoint、tokenizer/BPE、解码器、beam、热词/上下文、采样率/重采样、VAD、窗口长度、检测后去重/冷却逻辑和软件版本。
2. 说明当前分数是完整句 exact match、关键词命中、ASR 输出率、人工判断还是原始置信度；列出每个分数的分子、分母。
3. 对唤醒检测任务导出连续分数和最终触发事件。高分应统一表示更像目标词；若底层分数越低越可信，导出前转换方向。
4. 负例的误触发要在实际去重/冷却后的事件流上统计，避免重叠滑窗重复计为多个报警。

### B. 采集计划

- 试点：每词至少 20 名说话人，每人每词自然说 5 次。仅用于找错误和校准流程，不用于最终结论。
- 定版起始量：至少 50 名未参与训练的说话人，每人每词 10 次正例；目标口音、设备、房间、距离、噪声、自然/快速语速分层。50 人是工程起始量，不是统计功效保证；定版前按 FRR 目标与置信区间精度进一步算样本量。
- 负例：先为每词采集至少 100 小时覆盖自然场景的连续音频以筛查明显风险；若要求极低误唤醒率，应按误报警计数模型增加小时数。近邻词、普通句中提到目标、相似姓名与日常命令单独作为 hard-negative 测试集，并与自然负例分别报告。
- 每位说话人随机朗读短语顺序，不连续重复同词；自然语气为主。录音只使用匿名 speaker_id，避免把姓名或联系方式写入 CSV。
- 所有短语保持同一设备和条件的采集比例，保证候选公平比较。

### C. 切分与防泄漏

按 speaker_id 切分 train/dev/test，例如 60/20/20；同一个说话人、原始录音和其增强版本不得跨集合。微调只使用 train；阈值与方案只在 dev 调整；test speakers 必须独立且封存。对于已训练的模型，应保证最终测试说话人没有出现在微调语料里。所有候选使用同一测试说话人，便于配对比较。

### D. 主指标与置信区间

- FRR = 漏触发的正例 / 正例总数；同时报告 recall = 1 - FRR。
- FAR_clip = 误触发负例 / 负例片段数。
- FA/hour = 去重后的误触发事件数 / 负例音频小时数。
- dev 上扫描阈值，选择满足预先设定 FA/hour 上限时 recall 最大的阈值；README 示例为每小时 0.1 次，这只是占位目标，须按产品用途调整。
- 固定阈值到 test，不得用 test 调阈值。报告 test 的 FRR、FA/hour、分层结果和阈值。
- FRR 与 clip FAR 给 Wilson 95% 区间；同一人多条录音相关，另按说话人做 cluster bootstrap 区间。FAR/hour 的事件数区间应按 Poisson 计数或 speaker/session cluster bootstrap 报告。
- 若 test 负例 0 次误报警，不能称风险为零；粗略 rule-of-three 上界约为 3/T（T 为负例小时），仅作简单 Poisson 近似。报告真实负例时长。
- 多候选以同一批 test speakers 做配对差值和 speaker bootstrap；不要仅凭两个区间是否重叠来宣称显著。
- 分层报告口音、设备、距离、噪声和语速；避免整体平均掩盖某类用户失效。

## 换词依据

在看最终 test 结果前写下产品 FRR 上限、FA/hour 上限与非劣效界。按以下判据决策：

- 保留：目标 FA/hour 下 test FRR 的置信上限满足产品要求；主要说话人/场景没有明显退化；阈值 bootstrap 稳定。
- 补数据后复测：错误集中在可明确采集的读音或环境；在 dev 上补充代表样本改善；test 仍封存，追加新的独立说话人复测。
- 换词：目标发音在人群中无法统一、与另一个候选或高频日常词持续混淆、或目标误唤醒工作点下 FRR 跨场景持续超标。
- 无法判断：样本/负例时长不足、置信区间过宽、切分泄漏或指标定义不一。此时要补证据，而不是硬排“最难”。

候选打分可用于初筛，建议只包含：FRR@目标FA、FA/hour、speaker 间方差、与实际 hard negatives 的混淆率、发音一致性及采集覆盖。权重在最终测试前确定，且报告分项，不能用一个综合分掩盖风险。

## 运行

Python 3.9+，无第三方依赖。按 data/template.csv 格式把真实 detector 输出写入 CSV，在本目录运行：

    python evaluate.py data/your_scores.csv --target-fa-per-hour 0.1 --bootstrap 2000 --out results

脚本只用 dev 选阈值，在 test 上输出 summary.json 和 dev 阈值曲线 CSV。它假设一行代表一个不重叠样本或合并后事件；每个候选的 dev/test 都需要正负例。样本 CSV 是格式示例，不是实验数据。

## 参考

- icefall 上游仓库：<https://github.com/k2-fsa/icefall>
- NIST KWS evaluation plan：<https://www.nist.gov/document/kws15-evalplan-v05-comparedto-v04pdf>
- NIST KWS 评估定义和 miss/false alarm trade-off：<https://www-nlpir.nist.gov/projects/tv2010/Evaluation-cbcd-v1.3.htm>
- Zipformer paper：<https://arxiv.org/abs/2310.11230>


## 你下载的 GigaSpeech KWS 包：模型专属提示

我检查了给出的目录：它包含 commands_small/large.txt、BPE 500 tokens、exp/kws 和 exp-finetune/kws 的 metric/errs/recogs 日志及 pretrained.pt。icefall 上游的 egs/gigaspeech/KWS/RESULTS.md 说明该 Zipformer 是以 GigaSpeech XL 训练的通用 ASR/关键词模型；公开基准正例来自 open-commands，负例使用 GigaSpeech 测试音频。上游同时展示了增训的典型取舍：small set 上原模型 FN 43/307、Recall 86%、40 小时负例 1 次误触发（0.025/h）；finetune 后 FN 4/307、Recall 98.7%，但 FP 24 次（0.6/h）。所以“召回上升”不能单独作为唤醒词更好的结论，必须同时看负例暴露时长和误触发。

上游 KWS 的 run.sh 用 zipformer/decode.py，并传入 keywords-file、keywords-score 和 keywords-threshold。你对同一测试清单按多个 threshold 重复 decode，分别在独立 dev/test 上生成每个候选的 TP/FP/FN/TN 汇总，再录入 data/icefall_sweep_template.csv。scripts/evaluate_icefall_sweep.py 会在 dev 上选择满足 FA/hour 约束且召回最高的阈值，并在 test 上固定评估。它使用的是上游 metric 汇总，不要求你先导出逐帧连续分数。

操作步骤：
1. 把六个唤醒词放入与 icefall 关键词文件格式一致的自定义关键词文件，先检查 BPE/token 输出；不要改用原来 commands 的 positive 评估文件当作 hey 词测试。
2. 准备按说话人隔离的 positive dev/test 清单，以及有确定小时数的 negative dev/test 音频。每个候选使用同一组说话人和场景。
3. 使用你当前预训练/finetune checkpoint，保持 epoch/avg、chunk-size、left-context、keywords-score、设备、关键词处理和后处理一致，仅改变 threshold；建议先在 dev 扫描一个覆盖实际配置的阈值网格，然后把选出的阈值原样用于 test。
4. 把 icefall metric 文件中每个短语的 TP/FP/FN/TN 和该 test negative set 的小时数填入 CSV。确认每个 threshold 都使用同一 positive/negative 清单；若 metric 只输出整体 counts 而没有逐候选区块，应对关键词逐个单独解码或从 errs 日志手工建立逐词统计。
5. 运行：python scripts/evaluate_icefall_sweep.py data/icefall_sweep_template.csv --target-fa-per-hour 0.1 --out results/icefall-sweep.json
6. 对 FN/FP 对照对应 errs/recogs 结果人工标记音素/边界/近邻词原因，再根据上文 Go/Hold/Replace 判据决定增训还是换词。

0.1 次/小时是示例上限，不是对你产品的承诺；负例小时数不足时无法证明这么低的误报警率。阈值网格必须覆盖模型实际能触发的分数范围。这个汇总脚本计算片段 FAR 的 Wilson 区间，但 FA/hour 的区间还应根据原始误报警计数和负例暴露时长按 Poisson/会话聚类方法另外计算。示例 CSV 仅说明格式，不能当作模型结果。


