# 固定参数下的唤醒词声学筛选实验

## 这次要回答的问题

我们只比较唤醒表现和可观察的声学因素。按你确认的口径，当前六个分数来自相同参数，因此可作为同一条件下的初筛排序：

| 短语 | 当前唤醒分数 | 比 hey google 低 |
|---|---:|---:|
| hey google | 0.936 | — |
| hey tesla | 0.895 | 4.1 个百分点 |
| hey siri | 0.865 | 7.1 个百分点 |
| hey eva | 0.756 | 18.0 个百分点 |
| hey even | 0.553 | 38.3 个百分点 |
| hey ixio | 0.331 | 60.5 个百分点 |

所以当前的同参数结果已经把 Eva / Even / Ixio 排在明显较难的一组。接下来的实验要确认差距是否能在同一说话人、同一条件下复现，并找到错误集中在哪个音段。样本数未知，因此现阶段不声称统计显著。

## 为什么 Eva / Even / Ixio 值得做声学验证

### 共同假设：目标词首部以元音开头

在常见英语读法中，hey google、hey tesla、hey siri 的目标词分别以 /g/、/t/、/s/ 等辅音起始；Eva、Even、Ixio 的常见或可能读法更可能以元音起始。固定前缀 hey 后，辅音起始通常提供一个清晰的声学边界；若 hey 的尾元音直接连到目标词首元音，边界可能变模糊，模型更容易漏掉目标词起点。

这是对现有分数的可检验声学假设，不能仅靠拼写证明。实验要标注 hey/目标词边界、目标首音和触发时间，并验证低分样本是否集中于这些位置。

### hey eva：0.756

Eva 常见读音有 /ˈiːvə/、/ˈɛvə/ 等。重点查三个位置：

- hey 的 /eɪ/ 到 Eva 首元音之间是否连读或合并；
- Eva 首元音在说话人之间是否一致；
- /v/ 后面的弱尾音是否被短窗口、快语速或噪声影响。

若固定读法后，漏唤醒集中在 hey/Eva 边界或一种可补采的元音变体，Eva 仍可通过补样本改善；若多种读法导致同一名字呈现多个声学模式，则不适合作为稳定唤醒词。

### hey even：0.553

Even 常见读音约为 /ˈiːvən/，与 Eva 的可能读法共享 /iːv/ 起始。系统可能主要依靠后面的 /n/ 与 Eva 区分；若末尾被噪声、截断或窗口边界吞掉，两者容易出现相同声学前缀。

要检验的证据是：Even 的 FN 是否集中在末尾 /n/，以及 hey Eva 和 hey Even 是否在同一说话人上相互混淆。分别报告完整音频和尾部弱化/截断诊断结果；人工截断只用于定位机制，不代替自然录音成绩。

### hey ixio：0.331

Ixio 没有从拼写就能确定的统一英语读法。可能读成不同元音或音节数。对 KWS 而言，同一个目标如果被不同人读成不同音素序列，会让正例声学分布变宽，固定阈值下更容易漏唤醒。

第一步不是改模型，而是做盲读一致性实验：不提供示范，让说话人读 Ixio，人工记录音节数和 IPA/近似音素；再给统一示范读音重复测试。若标准发音后命中率明显变高，主要瓶颈是读音约定；若仍低且错误集中于特定音段，再考虑模型数据覆盖。

## 先预注册实验设置

比较期间固定并记录：checkpoint、解码器、关键词分词/发音序列、阈值、beam、chunk/窗口、VAD、音频采样率、麦克风、距离、增益、触发后去重逻辑。六个短语的任何候选专属阈值、声学增益或后处理都不能单独调整。

每个候选与对照必须用同一批说话人、相同次数和相同采集场景。将短语顺序随机化；同一个人不要连续反复念同一个词。模型每次是否在规定延迟内触发记为 hit=1/0。保存模型原始分数、触发时间和音频条件，但主要比较使用固定阈值下的 hit 率。

## 两阶段实验

### 第 1 阶段：快速筛选新词

每个候选 12–15 位说话人，每人自然说 5 次，共 60–75 条；包含安静环境和一种轻度背景噪声。每位说话人都说同一个已知对照词（建议 hey google，或你们业务认可的现有词），顺序随机。

同时做发音一致性记录：候选词首音类别、音节数、主要元音/辅音变体、说话人之间的读音一致比例。对 Ixio 先盲读，再统一示范读一次。

快速判读规则（工程筛查线，不是通用标准）：

- **绿：进入下一轮**：发音读法基本一致，命中率不比对照低超过 10 个百分点，且安静/噪声两种条件没有明显崩塌。
- **黄：补样本或规范读音**：与对照相差 10–15 个百分点，或主要由一种发音变体/一种环境造成漏唤醒。
- **红：优先淘汰**：比对照低至少 15 个百分点，且说话人配对差值的 bootstrap 区间仍显示该候选更差；读音难统一、跨条件持续低命中也可直接列为红色风险。
- 样本太少、区间很宽时写“未定”，不要把 60 条录音当作最终证明。

当前结果按对照差值已是：Eva −18.0pp（红旗/复核）、Even −38.3pp（强红旗）、Ixio −60.5pp（最高优先淘汰验证）。最终结论仍应由同说话人快速实验及置信区间确认。

### 第 2 阶段：正式声学确认

每个保留候选至少 30 位未参与微调的说话人，每人每词 10 次：5 次安静、5 次轻度噪声或稍远距离，共 300 次/词。保持同一说话人对所有候选都录制，形成配对数据。若要评估口音泛化，按目标口音分层并保证各词覆盖相同人群。

对各词报告：
1. 固定阈值的总命中率及 95% 置信区间；
2. 以 speaker 为单位的平均命中率及 cluster bootstrap 区间；
3. 相对 hey google 的同说话人配对差值和 bootstrap 区间；
4. 安静与噪声/距离分层命中率；
5. 触发延迟的中位数和高分位数；
6. 漏唤醒的人工音段原因：hey/目标边界、目标首元音、内部辅音、尾音、语速、音量、噪声、VAD/切窗。

若任务定义是“能否唤醒”，建议按触发事件判 hit，不要用 ASR 是否逐字转写整段来替代。

## 新词快速验收表

| 维度 | 怎么量 | 风险信号 |
|---|---|---|
| 发音一致性 | 多人盲读后记录音节/音素变体，统计主读法占比 | 同一拼写产生多种音节数/首元音 |
| 起始边界 | 固定前缀后检查首音触发时间及 FN 标注 | hey 后元音连读，漏检集中在目标起点 |
| 声学区分 | 与常见近音/相似词作同参数 hard-negative 对照 | 近音词也能触发，或候选间相互混淆 |
| 稳健性 | 相同说话人在安静/轻噪声/稍远场下重复 | 只有刻意慢读或近距离才成功 |
| 命中表现 | 固定阈值下命中率、说话人配对差值、置信区间 | 明显落后已知对照且跨条件持续 |
| 稳定性 | 说话人间命中率分布、每人最差场景 | 总平均高但一批说话人几乎无法唤醒 |

可把新候选和已知对照一起录制并通过 data/acoustic_pilot_template.csv 记录；使用 scripts/evaluate_fixed_wake.py 得到整体命中率、按场景结果、说话人 bootstrap 区间、相对对照配对差值和发音变体占比。它不会重新拟合阈值，因此能保持“同参数”比较。

## 用服务器上的 WAV 做同一套实验

你无需把 WAV 上传到本仓库。将每条完整唤醒语句保存为一个 WAV，在服务器上用当前实际唤醒链路、相同 checkpoint、阈值、窗口和后处理逐条运行，并导出每个文件是否在预设时限内触发（hit=1/0）、触发时间及实际模型分数。文件名或独立清单至少保留匿名 `speaker_id`、候选词、重复编号、录音条件和读音变体；原 WAV 不要重采样/归一化后覆盖，模型输入预处理应与部署一致。

1. 先按 `data/acoustic_pilot_template.csv` 收集逐条结果。每位说话人都录同一对照和所有候选，顺序随机；建议每词 12–15 人 × 5 次做快速筛选，正式确认至少 30 个未参与微调的说话人 × 10 次。每条都要用同一检测器和固定参数评分。
2. 运行 `python scripts/inspect_wavs.py <wav目录> --out wav_manifest.csv` 检查采样率、声道、时长、峰值、RMS 和削波比例。这是录音质量控制，不能把音量或波形统计直接当成唤醒难度。若候选和对照的录音条件不同，先重录或分层报告，不能用事后响度归一化掩盖采集差异。
3. 将模型逐条输出与清单合并为同一行一条 utterance 的 CSV，再运行 `python scripts/evaluate_fixed_wake.py data/your_trials.csv --control "hey google" --out results/acoustic-pilot.json`。脚本使用说话人配对统计，候选专属 threshold 不得调整。至少 10 名共同说话人才能给出绿/黄/红筛查标签；更少时标为证据不足。
4. 对所有漏唤醒逐条听音并标注 `miss_cause`：hey/目标边界、目标首元音/辅音、内部音、尾音、语速/音量、噪声、截断或其他。对 Ixio 先盲读，再做统一示范读音；两轮分开统计。可选用波形/频谱和人工时间戳记录目标起点、词尾及触发延迟，但对齐/标注人员应不知道模型结果，减少主观偏差。
5. 声学解释必须由“固定参数下命中率差异 + 同一批说话人配对结果 + 可复现的漏检位置/读音变体”共同支持。单看波形、音量、频谱或一个人的发音不能证明词难。若服务器可运行模型但无法导出逐文件结果，至少保存每条音频的模型触发事件和文件 ID；只有总分无法做逐音段诊断。

该流程适用于新候选：把新词加入相同的随机录音清单，与稳定对照一起采集，在相同说话人和条件下评分，再按相对差异、区间宽度、读音一致性及错误位置决定保留、补采还是换词。WAV 与逐条模型输出都留在你的服务器即可。

## 声学判别原则

一个词“难唤醒”的证据强弱依次为：

1. 同参数、同说话人、随机顺序重复后，命中率仍低；
2. 相对易唤醒对照的配对差异区间仍明显为负；
3. FN 集中在可解释的声学位置，并在不同人/条件重复；
4. 读音规范化或改变录音条件后，错误变化符合该声学假设；
5. 如果只能由拼写/词频解释，而音频与固定阈值命中没有相应证据，就不称为声学原因。

目前可以报告的是同参数分数排序和差值。下一步用配对实验确认；不要把未做音段标注的推测写成因果结论。

## 文件

- candidate-analysis.md：针对六个词的声学假设和实验解释。
- scripts/evaluate_fixed_wake.py：固定参数下的唤醒命中率与配对说话人分析。
- scripts/inspect_wavs.py：标准库 WAV 元数据/响度/削波 QC，不判断唤醒好坏。
- data/acoustic_pilot_template.csv：新候选快速试验数据模板。
- data/template.csv 与 evaluate.py：保留给能导出连续分数的场景；比较同参数唤醒时优先使用 fixed_wake 脚本。

## 参考

- icefall GigaSpeech KWS 配方和固定阈值解码参数：<https://github.com/k2-fsa/icefall/blob/master/egs/gigaspeech/KWS/run.sh>
- icefall 上游 KWS 结果（召回和误报警的权衡）：<https://github.com/k2-fsa/icefall/blob/master/egs/gigaspeech/KWS/RESULTS.md>
- NIST KWS 评估计划：<https://www.nist.gov/document/kws15-evalplan-v05-comparedto-v04pdf>

## 新增对照词试测结果：Neva 与 Kiva

用户报告的同轮试测分数：hey Neva = 0.758、hey Kiva = 0.664；已有 hey Eva = 0.756。Neva 与 Eva 只差 0.002（0.2 个百分点），实质上几乎相同；Kiva 比 Eva 低 0.092（9.2 个百分点）。相对 hey Google = 0.936，Neva 低 17.8 个百分点，Kiva 低 27.2 个百分点。

这组分数不支持“元音起始本身就是 Eva 低分主因，而辅音起始就会改善”的简单解释：/n/ 起始的 Neva 并未高于 Eva，/k/ 起始的 Kiva 反而更低。它说明不能把起始音类别当作单一难度指标。词内其他音段、发音一致性、声学覆盖、录音条件和样本波动都可能影响分数。下一步要检查同一说话人的配对命中结果，并标注漏唤醒落在 hey/目标边界、首音、内部音还是词尾。

样本数、逐条结果和漏检位置尚未提供，因此暂记为探索性观察，不宣称统计差异或因果结论。建议同一批说话人随机顺序重复录制 Eva、Neva、Kiva、Google，所有词重复次数相同并固定模型、阈值和处理参数。若 Neva 与 Eva 的配对表现及错误位置仍相近，应降低“元音边界是主因”的优先级；若 Kiva 漏检集中于 /k/ 起始或 hey/Kiva 边界，再用更多说话人检查爆破音释放、切窗和触发时限。

## 新候选词快速实验：以 hey google 为对照的完整操作示例

本节假设你收到的新候选是 **hey eva**，用表现稳定的 **hey google** 作配对对照。把 `hey eva` 换成任意新词即可复用。这里测的是实际唤醒器是否触发，不测 ASR 转写是否拼对。你已有的 Google=0.936 是历史分数；若它的录音人与候选、条件、分母不同，不能直接当本次对照。必须在本次试验里重新录 Google。

### 第 0 步：先写一张实验卡，冻结规则

开始录音前创建 `experiment_config.txt`，填写并保存：

```text
model_checkpoint: <实际部署的checkpoint路径或版本>
keyword/pronunciation config: <关键词配置、token/发音序列版本>
threshold: <当前部署阈值>
decoder/window/chunk/VAD: <当前值>
audio preprocessing: <采样率、声道、归一化等实际部署设置>
trigger deadline: <短语结束后允许的最晚触发时间>
speaker/device/distance/procedure: <本次采集约定>
primary outcome: 在trigger deadline内触发=1，否则=0
control: hey google
candidate: hey eva (替换为待测词)
```

照抄实际部署配置，不要为了让候选通过而单独改 threshold、增益、窗口或后处理。Google 和候选都用同一版本的模型与唤醒链路。若系统必须逐个加载关键词，逐词跑时仍要保持相同模型、阈值及其余参数，并对每个 WAV 单独记录检测结果。先确认系统对 WAV 的采样率/声道要求，录音时按要求保存原文件；不要先重采样或响度归一化覆盖母版。

### 第 1 步：准备参与者表和随机录音顺序

快速筛查找 **12–15 位说话人**。每位都录 Google 和候选，各 5 次，共每个词 60–75 条。要测两种条件时，每词每人安排 3 次安静、2 次轻度噪声，且两词分配完全一样；如果只能在安静环境做，就两词都只测安静，不要混入不平衡的噪声样本。

给每个人随机生成顺序，例如：

| 顺序槽 | 示例内容 |
|---:|---|
| 1 | hey eva / 安静 / 第 1 次 |
| 2 | hey google / 安静 / 第 1 次 |
| 3 | hey google / 安静 / 第 2 次 |
| 4 | hey eva / 轻噪声 / 第 1 次 |

上表只是示意；实际不要按“先念完所有 Google、再念所有 Eva”的固定顺序。每次念完停几秒再开始下一条，避免连续重复造成节奏/预期变化。参与者用 `S001`、`S002` 这样的匿名 ID，不在文件名或 CSV 中保存真实姓名。

### 第 2 步：按统一方式录 WAV

对每条音频给说话人相同指令：站在标记位置、对着同一麦克风，以日常音量自然说一次完整短语；不要故意拖慢、夸张咬字或重复说。安静/轻噪声条件按预先安排执行。不要挑选“最好听”的一次；所有有效录音都纳入，技术损坏（空文件、录错词、明显录制中断）要写明理由并重录，保留损坏记录。

建议一个 WAV 只包含一次目标短语及少量前后静音，避免在同一文件里连续喊 5 次。命名示例：

```text
S001_google_quiet_T01.wav
S001_eva_quiet_T01.wav
S001_eva_noise_T02.wav
```

另建录音清单，至少有 `file,candidate,speaker_id,trial_id,condition,pronunciation_variant`。对 Google 也照样记。Eva 若有不同读法，按实际听到的读法标注；读不确定写 `uncertain`，不要猜。发音一致性盲读可在正式唤醒录音前单独做一次，并另记结果，避免示范读音改变后续自然发音。

### 第 3 步：先做文件质量检查，再逐条跑实际唤醒器

在 WAV 所在机器或服务器上，对文件夹运行：

```bash
python scripts/inspect_wavs.py /path/to/wavs --out wav_manifest.csv
```

查看检查结果：Google 与候选是否都有文件、时长是否合理、采样率/声道是否一致、是否存在异常低电平或削波。这个工具只做文件和电平 QC，不会判断词难。发现采集故障时按预先规则重录，不要只删除候选的失败文件。

随后用第 0 步冻结的**实际唤醒系统**逐个处理 WAV。每条输出一行：原始文件名、实际命中的关键词、触发时间、系统分数（若有）、最终 hit。`hit=1` 的定义严格使用实验卡写好的截止时间；例如系统若规定短语结束后 800 ms 内触发，就 Google 和候选都用 800 ms。未触发、触发了错误词、超时触发均记 `hit=0`，另在备注中保留实际事件。不要用“识别文本看起来差不多”改判 hit。

### 第 4 步：合并逐条结果 CSV

把模型输出和录音清单按 WAV 文件名合并，另存 `data/trials.csv`。可以复制 `data/acoustic_pilot_template.csv` 作为起点，但要先删掉里面的两行示例数据，再换成你本轮全部真实试验。至少使用以下列名（与模板一致）：

```csv
candidate,speaker_id,trial_id,condition,hit,pronunciation_variant,miss_cause
hey google,S001,1,quiet,1,standard,
hey eva,S001,1,quiet,0,ee-vuh,hey/eva_boundary
```

实际文件名可以保留在额外的 `file` 列，便于回听，但不能漏掉上面的必需列。每个候选每位说话人应有相同的有效重复数。所有漏唤醒先记 `miss_cause=pending`，后面回听后改成 `hey_target_boundary`、`target_onset`、`medial_sound`、`word_final`、`noise`、`truncation`、`uncertain` 等一致标签。不要把成功样本的 `miss_cause` 填成漏检原因。

### 第 5 步：运行统计并逐项读结果

在工程目录运行（Windows PowerShell 也可把路径替换成 Windows 路径）：

```bash
python scripts/evaluate_fixed_wake.py data/trials.csv --control "hey google" --bootstrap 5000 --seed 2026 --out hey-eva-pilot.json
```

逐项检查输出 JSON：

- `hit_rate`：固定参数下所有录音的命中比例；例如 54/60 = 0.90。
- `clip_wilson_95`：把每条录音暂按独立样本算的区间；同一个人重复录音彼此相关，所以不能只报告它。
- `speaker_mean_hit_rate` 和 `speaker_cluster_bootstrap_95`：先算每个人的平均命中率，再以说话人为单位重抽样，更适合本配对试验。
- `paired_vs_control.mean_difference`：候选减去 Google 的同说话人平均差。`-0.12` 表示候选平均低 12 个百分点。
- `paired_vs_control.bootstrap_95`：配对差的说话人 bootstrap 区间。看差异方向和区间宽度，不要只比较两个词各自置信区间是否重叠。
- `conditions`：检查轻噪声是否明显比安静差；每个条件次数必须平衡。
- `pronunciation_variants`、`miss_causes`：检查发音是否分裂，以及漏检集中在哪里。

脚本把至少 10 名共同说话人作为给出筛查标签的最低条件。当前代码按配对均值差和区间给出红/黄/绿试点提示；这不是产品验收标准。建议人工核对 JSON 里的原始人数、分母和录音清单，防止缺行或标签拼写不一致。

### 第 6 步：按预先约定做决定

以下是快速试点用的暂定边界，单位均为百分点，最终要按产品能接受的漏唤醒率调整：

| 判读 | 本次如何操作 |
|---|---|
| 候选落后 Google ≤10pp，发音读法基本一致，安静/轻噪声无明显崩塌 | 暂时保留，进入更大规模确认；不等于已证明可上线 |
| 落后 10–15pp、区间很宽，或问题集中在某个读音/条件 | 暂不淘汰；按该问题补录，并用新说话人复测 |
| 配对平均差 ≤−15pp 且 bootstrap 区间上限仍低于 0；多种条件/说话人都重复出现 | 列为高风险候选，优先换词或做有针对性的诊断 |
| 共同说话人少于 10、数据缺失、控制与候选条件不平衡 | 结论写“证据不足”，修复采集后重做，不给红绿判断 |

回听漏检后再形成机制解释。例如 Eva 的差距若伴随多名说话人的漏检集中在 hey/Eva 边界，才支持边界假设；若错误分散在不同位置，就不能只凭元音起始解释。新增一个 Neva/Kiva 这样的对照时，仍需同批参与者、同次数、随机顺序和同参数；它们只能帮助定位原因，不能替代 Google 对照。

### 下次收到新词时，只需替换这些内容

把 `candidate` 从 `hey eva` 改成新短语；增加该词的标准发音及盲读记录；保留同一 Google 对照、采集顺序规则、命中定义、阈值和分析命令。不要复用上一轮 Google 的历史录音来代替同轮配对对照。WAV 与真实逐条输出可一直留在你的服务器，GitHub 只保存脚本、模板和不含隐私的汇总结果。

## 仅使用 Qwen TTS 时的具体执行版本

你当前不能录真人音频，因此本节是上面“说话人/录音”步骤的替代执行方式。此实验的统计单位是 **独立 TTS 音色配置（profile）**，不是人；结论只说明模型对这些合成语音的表现，不能直接推断真人用户的唤醒率。你之前的 hey google=0.936 不能替代本轮合成的 Google 对照。

### A. 先锁定生成配置

建立一份配置记录，Google 和新词共用同一设置：

```text
Qwen TTS checkpoint / API version:
voice or speaker profile ID:
reference voice prompt (if any):
language / instruction / emotion:
speed / pitch / sampling settings:
seed list:
output sample rate / channels:
wake model checkpoint / threshold / window / VAD:
trigger deadline:
```

实验中唯一有意改变的是目标词文本。不要给新词单独指定更清晰的语气、更慢语速或不同情绪。`Hey Google.` 与 `Hey Eva.` 使用完全相同的文本模板、大小写和标点，只替换目标词。如果应用实际使用的短语格式不同，照着应用格式生成并在整批中固定下来。

### B. 准备 profile × seed 配对表

快速筛查目标是 12–15 个不同的 Qwen 音色/说话人 profile，每个 profile 下 Google 与候选各生成 5 次，总计每个词 60–75 条 WAV。每一个 profile、每个生成轮次都要有一对音频（一个 Google、一个候选）。若只有一个 profile，可以先生成每词 20–30 个独立版本，观察该音色下的初步结果；但不能把这些版本称为 20–30 个说话人，也不能据此声称跨音色泛化。若 Qwen 的生成完全确定，重复相同设置可能得到重复波形；重复文件不算独立样本，应检查波形哈希/文件内容或试听确认确实有不同实现。

任务表建议包含：`tts_profile_id,candidate,trial_id,seed,condition,pronunciation_variant`。`condition` 初轮填 `clean`。示例：

```csv
tts_profile_id,candidate,trial_id,seed,condition,pronunciation_variant
Q001,hey google,1,101,clean,standard
Q001,hey eva,1,101,clean,ee-vuh
Q001,hey google,2,202,clean,standard
Q001,hey eva,2,202,clean,ee-vuh
Q002,hey google,1,101,clean,standard
Q002,hey eva,1,101,clean,ee-vuh
```

如 Qwen 支持随机 seed，预先固定 seed 列表；同一 profile 的 Google 与候选尽量配对使用同一 seed 序号，并让不同重复使用不同 seed。Seed 配对仅帮助控制生成设置，不代表两个生成波形有相同的音素实现。若需测噪声/房间条件，先用 clean 音频生成，再对 Google 和候选施加完全相同且预先固定的噪声处理；每种条件都平衡数量，单独报告。

### C. 批量生成、命名并质检

一次任务生成一个短语、一条 WAV；不要把多次重复拼在一个文件。建议命名：

```text
Q001_google_R01_seed101_clean.wav
Q001_eva_R01_seed101_clean.wav
Q001_google_R02_seed202_clean.wav
Q001_eva_R02_seed202_clean.wav
```

逐条确认实际生成内容、发音和文件可播放。若发现合成器漏词、读错目标词、文件空白/损坏，标记该条并按同设置重生成，Google 与候选都使用相同质检规则。运行：

```bash
python scripts/inspect_wavs.py /path/to/generated_wavs --out wav_manifest.csv
```

核对采样率、声道、时长、电平和削波。该脚本只做 QC，不评估发音自然度或唤醒难度。不要因为候选听起来不理想就只挑选 Google/候选中较好的生成版本；预先定义并对两者一致地处理无效音频。

### D. 用同一唤醒器逐文件评分

把所有生成的 WAV 文件名随机打乱后，逐条送入实际唤醒链路。模型、关键词配置方式、阈值、窗口、VAD、前处理及后处理保持一致。开始前确定 `trigger deadline`：若系统已有部署时限就照用；没有的话先选一个固定时限并写入配置，对 Google 和候选都使用它。每个 WAV 导出一行结果：文件名、命中的词、触发时间、原始分数（如可获得）、`hit`。只有在时限内正确触发目标才记 `hit=1`；未触发、触发错词或超时都记 `hit=0`，错误事件在备注中保留。

### E. 合并并分析

将 Qwen 任务清单与检测输出按文件名合并成 `data/trials.csv`。模板中 `speaker_id` 字段填 `tts_profile_id`（例如 Q001）；每个 profile 都必须同时有 Google 与候选。删除模板示例行后再放真实结果。每行代表一个 WAV，CSV 至少包含：

```csv
candidate,speaker_id,trial_id,condition,hit,pronunciation_variant,miss_cause
hey google,Q001,1,clean,1,standard,
hey eva,Q001,1,clean,0,ee-vuh,hey/eva_boundary
```

运行：

```bash
python scripts/evaluate_fixed_wake.py data/trials.csv --control "hey google" --bootstrap 5000 --seed 2026 --out hey-eva-pilot.json
```

在输出中把 `speaker_id` 理解为 TTS profile：`hit_rate` 是所有合成 WAV 的命中比例；`speaker_mean_hit_rate` 是各 profile 等权的平均命中率；`paired_vs_control.mean_difference` 是候选减 Google 的同 profile 差值，`-0.10` 表示低 10 个百分点；`bootstrap_95` 是按 profile 重抽样的区间。12–15 个 profile 仍是小规模筛选，置信区间可能较宽。

如果只有一个 Qwen 音色，不要给每个 seed 编造不同 `speaker_id` 来伪装 profile。此时可报告该音色下各词命中次数/总次数和不同生成轮次的波动；脚本会显示共同 profile 数不足，不给绿/红结论。想要按 profile 做有意义的 bootstrap，必须有多个真正独立的音色配置。

### F. 结论适用范围

如果 Eva 在多种 Qwen 音色下都低于同轮 Google，且漏检位置在多个 profile 中重复，说明该候选在**当前 Qwen TTS 合成分布 + 当前唤醒器**上有稳定风险，值得淘汰或做针对性训练。它仍不能单独证明真实人声也会有同样差距，因为 TTS 可能产生不自然但稳定的音段、停顿或韵律。工程报告要明确写“Qwen TTS 合成音频试验”；后续若能取得真人录音，应作为外部验证集，而不是与本次合成数据混在一起。


