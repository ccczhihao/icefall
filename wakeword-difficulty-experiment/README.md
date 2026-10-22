# Qwen TTS + icefall 唤醒词快速实验

## 本工程只处理什么

当前可用数据只有：

1. Qwen TTS 生成的 WAV；
2. Icefall 对这些 WAV 的结果：唤醒 / 未唤醒。

这里的“未唤醒”指 **音频里确实说了目标唤醒短语，但 Icefall 没有在规定时间内触发**。如果某个目录放的是没有说目标短语的普通语音，它不是本实验的“漏唤醒”样本，请不要和上述 WAV 混在一起。

本流程不要求真人录音，也不要求重新训练模型。目标是用同一批 Qwen 合成配置、同一 Icefall 唤醒参数，快速比较新词与 `hey google` 对照的合成音频命中情况，并检查漏唤醒 WAV 有哪些可观察差异。结论只适用于本批 Qwen TTS 音频和当前 Icefall 配置。

## 当前已报告分数

| 短语 | 用户报告分数 | 相对 hey google |
|---|---:|---:|
| hey google | 0.936 | — |
| hey tesla | 0.895 | -4.1 个百分点 |
| hey siri | 0.865 | -7.1 个百分点 |
| hey eva | 0.756 | -18.0 个百分点 |
| hey even | 0.553 | -38.3 个百分点 |
| hey ixio | 0.331 | -60.5 个百分点 |
| hey neva | 0.758 | -17.8 个百分点 |
| hey kiva | 0.664 | -27.2 个百分点 |

这是观察分数记录。当前没有每个分数的 WAV 数、Qwen profile/seed、逐条唤醒标签和分数定义，因此不能从表中算置信区间，也不能断言音素因果。Eva 与 Neva 仅差 0.2pp，Kiva 比 Eva 低 9.2pp；这表明“元音起始一定差、辅音起始一定好”不是可靠的单一规则。应使用下文的成对 WAV 实验继续判断。

## 实验要回答的问题

对一个新短语（例：`hey eva`），在当前 Qwen TTS 生成分布和固定 Icefall 参数下：

- 该词的合成 WAV 有多少比例成功触发？
- 同一 Qwen 音色配置、同一生成轮次下，它比 `hey google` 对照低多少？
- 漏唤醒音频是否集中在少数 profile/生成轮次，或有可复查的时长、电平、发音/边界差异？
- 当前结果够不够做初筛，还是需要更多合成样本？

## 先准备一份输入清单

将 WAV 放在服务器或本地任意目录。目录可以沿用 Icefall 的两个结果目录，例如：

```text
data/
  wake/
    Q001_google_R01.wav
    Q001_eva_R01.wav
  no_wake/
    Q001_eva_R02.wav
```

目录名仅表示 Icefall 的处理结果；不代表 `no_wake` 里的音频是普通负例。每条 WAV 应只含一个 Qwen 生成的完整短语。文件名最好编码出：

```text
<profile>_<candidate>_R<轮次>_seed<种子>.wav
Q001_google_R01_seed101.wav
Q001_eva_R01_seed101.wav
```

如果现有文件名没有这些信息，不要猜：先在清单里按文件路径逐条补录能确认的内容，未知值写 `unknown`。特别需要区分 Qwen 音色配置；同一音色生成 20 个文件仍是一个 profile，不是 20 个独立 profile。

建立 `data/trials.csv`，每条 WAV 一行；模板只有表头，复制后逐条填写。字段说明：

| 字段 | 填什么 | 示例 |
|---|---|---|
| `candidate` | WAV 中实际合成的完整短语，统一小写写法 | `hey eva` |
| `speaker_id` | Qwen TTS profile ID；未知时写 `unknown`，不要把 seed 冒充 profile | `Q001` |
| `trial_id` | 同一个 profile/短语下的生成轮次 | `1` |
| `condition` | 当前合成条件；只有普通 clean 音频就填 `clean` | `clean` |
| `hit` | Icefall 结果：按下面统一定义填 1 或 0 | `0` |
| `pronunciation_variant` | 从 WAV 听辨的实际读音；不确定写 `unknown` | `ee-vuh` |
| `miss_cause` | 漏唤醒 WAV 回听后标注；命中样本留空 | `target_onset` |

示例：

```csv
candidate,speaker_id,trial_id,condition,hit,pronunciation_variant,miss_cause
hey google,Q001,1,clean,1,standard,
hey eva,Q001,1,clean,0,ee-vuh,hey_target_boundary
```

Icefall 的“唤醒”统一记为 `hit=1`，“未唤醒”记为 `hit=0`。如果系统对一个 WAV 可能多次触发，仍按该 WAV 是否在预先固定的触发时限内至少正确触发一次来记；同一时限也应用于所有短语。若没有触发时限记录，本轮先使用 Icefall 已有最终二分类结果，不要事后改判。

## 逐步执行

### 第 1 步：确认这一批 WAV 能公平比较

先对照文件名和 Icefall 结果，确认：

- 每个 WAV 只对应一个短语；
- `hey google` 和待测词都在本批数据中，且通过同一 Icefall checkpoint/阈值/解码与后处理；
- Google 和候选尽可能来自相同 Qwen profile、相同生成轮次/seed、相同合成设置；
- 结果目录中的每个 WAV 都能找到唯一的一行标签，不能漏文件、重复计数或把文件名相似但路径不同的音频合并；
- 如果 Icefall 配置、Qwen 模型或生成设置中途变过，按配置版本拆开统计，不能混成一个总命中率。

如果本批没有重新生成的 Google WAV，旧分数 0.936 只能当历史参考。为了配对比较，应使用同一批 Qwen profile 和生成设置重新得到 Google 对照结果。

### 第 2 步：生成下一批新词 WAV（未来每个候选都这样做）

用 Qwen TTS 生成目标短语和 `hey google`，只替换关键词，其它输入尽量固定：

1. 固定 Qwen checkpoint/API 版本、voice/profile、参考音频或 voice prompt、语言、指令、语速、情绪、采样设置、seed 列表和输出格式。
2. 固定文本模板，例如始终用 `Hey Google.` 对 `Hey Eva.`；只替换 Google/Eva。不要只给候选词增加慢速、重读或有利的 prompt。
3. 用多个真正不同的 TTS profile 做快速初筛；建议 12 个以上 profile，每个 profile/候选生成 5 条独立 WAV。Google 同样每个 profile 生成 5 条，形成配对。若只能用一个 profile，可生成 20–30 个不同生成轮次，但结论只限该音色，不声称跨音色稳定。
4. 如 Qwen 的输出确定性很强，确认不同轮次不是同一个音频的拷贝。完全重复的文件不能当作独立重复。保留 profile、seed、轮次和原始生成文件名。
5. 先用 clean 语音比较。要测噪声时，把完全相同的噪声处理施加到每个词，并单独标记条件；不要只处理候选。

### 第 3 步：检查 WAV 和 Icefall 标签

运行 WAV 质量清单工具：

```bash
python scripts/inspect_wavs.py /path/to/wav_root --out wav_manifest.csv
```

检查输出中的时长、采样率、声道、RMS、峰值和削波。它只发现文件质量差异，不判断唤醒难度。若候选文件普遍比 Google 短很多、电平极低或有大量削波，先确认这是 Qwen 生成差异还是文件处理问题；不要静默删掉失败文件。只对两边使用同一套事先定义的损坏文件处理规则。

随后逐一核对 Icefall 结果：每个 WAV 对应的 hit 是否和“唤醒/未唤醒”目录一致。目录标签与日志冲突时，以 Icefall 逐文件日志为准并调查原因，不要凭目录名强行覆盖。

### 第 4 步：建立一行一条 WAV 的 CSV

把 Qwen 任务清单、文件路径和 Icefall 逐文件唤醒结果合成 `data/trials.csv`。需要逐条填写，不要只填每个词一个汇总分数。模板已包含 `file`、`seed`、`icefall_score`、`trigger_time_ms` 列，方便回查；分析脚本会读取模板中的核心列。

快速检查：

- 每行的 `candidate` 与短语一致；
- `hit` 只能是 0 或 1；
- 每个 profile 下 Google 和候选均有记录；
- 不能把不同 Icefall 配置混在一起；
- 若 profile/seed 缺失，明确写 `unknown`，并接受分析结论会受限。

### 第 5 步：计算每个词的命中和配对差

在工程目录运行：

```bash
python scripts/evaluate_fixed_wake.py data/trials.csv --control "hey google" --bootstrap 5000 --seed 2026 --out wakeword-summary.json
```

重点看输出：

- `trials`、`hits`：分母和命中数。先手工验证命中率 = hits / trials。
- `hit_rate`：该词在本批合成 WAV 上的命中率。
- `speaker_id` 在本实验表示 Qwen profile。profile 多于一个时，`speaker_cluster_bootstrap_95` 是以 profile 为单位的区间。
- `paired_vs_control.mean_difference`：候选 profile 平均命中率减 Google profile 平均命中率；`-0.10` 是低 10 个百分点。
- `paired_vs_control.bootstrap_95`：成对差值区间。如果区间很宽或包含 0，结果不稳定/证据不足。
- `conditions`：若有多个合成处理条件，分条件检查；条件不平衡时不要直接比较总分。
- 发音变体与 `miss_causes`：看漏唤醒是否集中在某类合成读法或某个音段。

若只有一个 profile，脚本可显示原始命中率，但不能提供跨 profile 的可靠区间，也不应使用绿/红标签。不要把不同 seed 当成不同 profile 来制造窄置信区间。

### 第 6 步：回听“唤醒”和“未唤醒”两组 WAV

对每个候选分别随机抽取若干唤醒和未唤醒 WAV，按相同音量播放比较。至少记录：

- Qwen 实际把目标词读成什么；同一个词是否有多种读音；
- `hey` 结尾到目标词开头是否连在一起；
- 未唤醒样本与成功样本相比，差别是否反复出现在目标首音、词中或尾音；
- 是否存在异常停顿、目标音节缺失、语速变化或文件截断；
- Icefall 触发时间是否系统性偏晚（若日志有时间戳）。

把漏唤醒原因填进 `miss_cause`，用固定标签如 `hey_target_boundary`、`target_onset`、`medial_sound`、`word_final`、`pronunciation_variant`、`truncation`、`uncertain`。不要只挑一个符合预期的失败例子；统计所有失败 WAV，命中 WAV 也抽样复核。WAV 时长、RMS 或主观听感只能帮助找线索，不能单独证明因果。

### 第 7 步：按同一规则判断新词

初筛可暂用以下工程规则（不是统计学/产品通用标准）：

| 结果 | 下一步 |
|---|---|
| 候选命中率与 Google 相差不超过 10pp；profile 配对区间没有明显劣化；各 profile 发音稳定 | 暂时保留，增加新生成轮次复核 |
| 差 10–15pp、区间宽，或命中只在某些 profile/读音变体下降 | 暂不定；检查漏唤醒 WAV，按相同设置补生成，并单独报告变体 |
| 配对平均差 ≤−15pp，区间上限仍低于 0，且多个 profile 都出现 | 标为当前 Qwen TTS 条件下的高风险词，优先换候选或做目标音段诊断 |
| profile 不匹配、模型配置变更、结果缺失，或只有一个 profile 但要推断一般性 | 结论写“证据不足/仅限该 profile”，不要硬分级 |

你已有的数据可先计算逐条命中率，并按上述配对流程补充新一轮 Google 对照。Eva/Neva 分数接近、Kiva 更低，当前足以提醒我们“起始元音/辅音”不是单独可靠的换词规则；要依赖同 profile 配对结果和失败 WAV 的重复声学模式。

## 参考文件

- `scripts/evaluate_fixed_wake.py`：输入逐条 hit，输出命中率和 profile 配对 bootstrap。
- `scripts/inspect_wavs.py`：生成 WAV 元数据/响度 QC 清单。
- `data/acoustic_pilot_template.csv`：逐 WAV 标签空模板。
- Icefall GigaSpeech KWS 解码配置：<https://github.com/k2-fsa/icefall/blob/master/egs/gigaspeech/KWS/run.sh>

