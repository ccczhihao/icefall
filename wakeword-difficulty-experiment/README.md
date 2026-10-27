# Icefall KWS 唤醒词难度筛查

## 五个词增训后的观察

你报告 Kiva/Neva/Ixio/Even/Eva 增训后命中率分别为 0.890/0.907/0.897/0.642/0.837。相较原始模型，分别提升 22.6/14.9/56.6/8.9/8.1 个百分点。Ixio 的大幅恢复表明原始模型低分不能直接当作词语固有声学难度；当前增训结果中 Even 最低，值得优先检查训练覆盖和独立测试表现。详细差值、解释边界及下一步检查见 [候选词结果分析](candidate-analysis.md#五个候选词增训后的结果)。

该解释假设两轮结果的测试集、KWS 命中定义和阈值策略可比；请报告每词命中数/测试数，并确认测试 WAV 未参与增训。若只测了含关键词音频，这些分数应称为命中率/召回率，不包含误唤醒表现。

## 实验对象与目标

这是 **KWS（关键词唤醒）评测**：使用 Icefall 的 GigaSpeech 原始 ASR 训练模型作为当前 KWS 流程中的模型，**没有做 KWS 增训**。`wake` / `no_wake` 是 Icefall KWS 对每条 WAV 给出的触发结果。命中率的定义是 KWS 触发数除以该候选的 WAV 总数；不是 ASR 转写文本是否包含目标短语。

你已经逐条听过这些 WAV，并确认目标词发音没有问题。因此本流程不把 Qwen 合成质量、发音变体或听辨任务列为解释因素，也不要求你逐条填写 profile、seed、发音或 miss cause。音频只用于自动提取少量客观波形特征，与 KWS 命中/未命中结果做描述性比较。

实验回答两件事：

1. 在**同一 Icefall KWS 模型和参数**下，新候选的触发率相对 `hey google` 差多少？
2. 触发与未触发的 WAV 在时长、RMS 电平、峰值、过零率等可自动测量的声学量上是否呈现稳定差异？这些量只用于找线索，不单独证明原因。

此外，BPE 切分和 GigaSpeech 训练文本出现次数作为模型侧的背景信息单独记录。它们不能替代 KWS 触发率，也不能单凭相关性说明声学原因。

## 已有结果

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

以上按你提供的 Icefall KWS 结果理解。由于暂缺各词 WAV 数和逐条标签，不能从这些汇总分数重算区间或判断显著性。Eva/Neva 接近、Kiva 低于 Eva，说明仅用“词首是元音还是辅音”无法可靠筛词；新候选应经过同配置 KWS 实测。

## 最少操作版：只整理目录，然后运行一个脚本

### 第 1 步：整理 Icefall 已经输出的 WAV

把 KWS 唤醒和未唤醒 WAV 复制或放入下面结构。每个候选建一个子目录，目录名用候选词；空格可以写成下划线。**不需要改文件名、不需要逐条填 CSV。**

```text
results/
  wake/
    hey_google/       # KWS 唤醒 WAV
      google_001.wav
      google_002.wav
    hey_eva/
      eva_001.wav
  no_wake/
    hey_google/       # KWS 未唤醒 WAV
      google_003.wav
    hey_eva/
      eva_002.wav
      eva_003.wav
```

文件必须按 Icefall 对应 WAV 的实际 KWS 结果放入 `wake` 或 `no_wake`。脚本会检查 WAV 能否读取；损坏或无法解析的文件会列入错误，不会悄悄计入分母。不同模型 checkpoint、关键词参数或阈值产生的结果请分开放在不同根目录，不能混合统计。

### 第 2 步：运行自动汇总

在工程目录运行：

```bash
python scripts/summarize_kws_folders.py /path/to/results --control hey_google --out kws_summary.json
```

Windows 示例：

```powershell
python scripts/summarize_kws_folders.py "D:\kws_results" --control hey_google --out kws_summary.json
```

脚本自动完成：

- 按候选统计 WAV 总数、唤醒数、未唤醒数和 KWS 命中率；
- 计算相对 `hey google` 的百分点差及逐 WAV Wilson 95% 区间；
- 分别对唤醒与未唤醒 WAV 汇总平均时长、RMS、峰值和过零率；
- 保存完整 JSON 报告，并列出无法读取的文件。

输出中的 `delta_vs_control_pp=-18` 表示候选触发率比 Google 低 18 个百分点。脚本使用逐 WAV 区间，若 WAV 来自相同录制批次、重复拷贝或有其它相关性，该区间可能偏窄；当前没有 profile/seed 元数据时，不把 WAV 当作独立说话人，也不声称能估计跨说话人表现。

### 第 3 步：按固定规则比较候选

测试时应确保候选和 Google 使用完全相同的 Icefall KWS checkpoint、阈值、keyword score、解码参数、音频预处理及触发判定。每个候选尽量使用相同 WAV 数量；若数量不同，报告分母并以命中率和区间共同判断。不要为单个候选单独调低阈值。

可用下列**初筛**规则，不是普适产品门槛：

| 观察结果 | 初筛处理 |
|---|---|
| 候选与 Google 相差不超过 5 个百分点，区间也未显示明显劣化 | 暂时保留；后续扩大样本复测 |
| 低 5–15 个百分点，或区间很宽/与 Google 重叠较多 | 暂列待定；增加同条件 WAV 后再判 |
| 低至少 15 个百分点，且区间整体低于 Google，重复一批仍如此 | 当前模型/KWS 配置下列为高风险，优先比较其它候选 |
| Google 对照缺失、参数不一致、文件数太少或结果目录无法确认 | 证据不足，补齐公平对照再判 |

阈值用于快速排序候选，不代表最终唤醒产品的误报/漏报验收标准。本实验只有目标词正例 WAV，没有背景负例，因此不能评价误唤醒率。

## 如何用结果分析声学难易

### 1. 先看 KWS 触发率

这是直接回答“当前模型能否稳定唤醒”的首要指标。比较候选与 Google 的命中率差、样本数和区间。若 `hey even` / `hey ixio` 在同一配置下持续低于 Google，这能说明它们在**当前这批目标词测试 WAV 和当前 KWS 系统**上更难触发，但不能泛化为所有用户或所有录音条件。

### 2. 再看未唤醒和唤醒 WAV 的自动波形统计

JSON 的 `acoustics_by_kws_outcome` 按实际 KWS 结果分组比较：

- `mean_duration_s`：整段时长；
- `mean_rms_dbfs`：平均有效值电平；
- `mean_peak_dbfs`：峰值电平；
- `mean_zero_crossing_rate`：过零率，粗略反映波形快速变化程度。

如果某候选的未唤醒音频在某项指标上持续偏离该候选的唤醒音频，可以把它记为进一步检查的线索。它不能单独证明 KWS 失败由该特征引起；尤其不同词之间的绝对时长或电平差异，可能只是音频本身差别。无需为此再逐条听音或填写 miss cause。

### 3. 分开看模型文本因素：BPE 与训练语料

使用模型包的 `bpe.model` 对候选完整短语编码，记录 piece 序列、piece 数及 UNK。命令如下（在已安装 SentencePiece 的环境运行）：

```bash
python scripts/analyze_bpe_candidates.py --model "<bundle>/data/lang_bpe_500/bpe.model" --tokens "<bundle>/data/lang_bpe_500/tokens.txt" --phrases "hey google" "hey eva" "hey even" "hey ixio" "hey neva" "hey kiva" --out bpe-candidates.json
```

`tokens.txt` 的整数是 token ID，不是训练频次。已检查到 `▁EVEN` 的 ID 为 274，这只说明有对应词首 piece。其他候选也可能正常拆成多个子词；需用模型编码结果判断，不能仅看整词是否出现在 token 文件。

如果能取得与该模型训练相对应的 GigaSpeech 训练转录文本，再按词边界统计候选词及完整短语次数；没有训练文本时填“未知”，不要拿 BPE ID 代替词频。低 KWS 触发率与较多 BPE pieces 或较低词频并存，只能说明可能相关，不能证明是哪一因素造成。

## 报告中建议保留的最少信息

每次实验只需保存：

1. 原始 `wake/`、`no_wake/` WAV 目录；
2. 使用的 KWS checkpoint、threshold、keywords-score 和其它关键配置（写在一个 `experiment-notes.txt` 即可）；
3. `kws_summary.json`；
4. 可选的 `bpe-candidates.json` 和训练文本词频结果（有资源时）。

不需要手工创建逐 WAV CSV，不需要记录 Qwen profile/seed，不需要主观标注发音或漏唤醒原因。若后续要分析模型分数随阈值变化，再额外导出 Icefall 的逐 WAV 原始分数；当前只有唤醒/未唤醒分类时，脚本不会虚构分数或因果解释。

## 工程文件

- `scripts/summarize_kws_folders.py`：按目录标签自动统计 KWS 命中率和 WAV 声学描述量。
- `scripts/inspect_wavs.py`：单独导出 WAV 元数据清单（可选）。
- `scripts/analyze_bpe_candidates.py`：用 SentencePiece 模型检查候选 token 序列（可选）。

Icefall 的 GigaSpeech KWS 解码脚本可参考：<https://github.com/k2-fsa/icefall/blob/master/egs/gigaspeech/KWS/run.sh>。

