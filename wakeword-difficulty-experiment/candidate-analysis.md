# Qwen TTS 合成唤醒结果：候选词观察与声学诊断

## 数据范围

当前实验输入限定为 Qwen TTS 生成的目标短语 WAV，以及 Icefall KWS 对逐条音频给出的唤醒/未唤醒结果。该 KWS 使用 GigaSpeech 原始 ASR 训练模型，未做 KWS 增训。没有真人录音，也没有负例背景语音。下列观察因此只描述已测试合成音频与当前 Icefall 配置；不能外推真人用户表现，也不能评估误唤醒率。

## 已报告结果

| 唤醒短语 | 分数 | 与 hey google 的差值 |
|---|---:|---:|
| hey google | 0.936 | — |
| hey tesla | 0.895 | -4.1pp |
| hey siri | 0.865 | -7.1pp |
| hey eva | 0.756 | -18.0pp |
| hey even | 0.553 | -38.3pp |
| hey ixio | 0.331 | -60.5pp |
| hey neva | 0.758 | -17.8pp |
| hey kiva | 0.664 | -27.2pp |

这些是用户报告的汇总数。每词 WAV 数、profile/seed、逐条 Icefall 标签和分数定义没有完整记录，所以不能算统计区间或显著性。若数值确实是 Icefall KWS 每条合成 WAV 的唤醒率，排序显示 Eva、Even、Ixio 低于 Google；需要用逐条结果复算并确认每词分母一致。

## 现阶段可以说什么

- Neva=0.758 与 Eva=0.756 几乎相同；Kiva=0.664 比 Eva 低 9.2pp。因此“元音起始一定更难、加辅音起始就会更容易”不适合作为单一判断规则。
- Even 与 Eva 可能有相似词首，而词尾不同；可在未唤醒 WAV 中检查差异是否反复落在词尾。但在没有逐条试听/标注前，这只是待验证假设。
- Ixio 的发音是否一致，应直接从不同 Qwen profile/seed 生成 WAV 中核对。若读音发生变化，应区分 TTS 发音变体与 Icefall 漏唤醒；不要把文本拼写直接当成实际声学读音。
- 汇总命中率说明“哪些分数低”，不能说明“为什么低”。原因分析需要对比同 profile 的成功/失败音频、生成条件和 Icefall 触发时间。

## 回听标签建议

对每个候选的唤醒与未唤醒 WAV 成对抽听，使用一致标签：

- `hey_target_boundary`：hey 尾部与目标词开头连读/边界不清；
- `target_onset`：目标词首音弱化、缺失或不稳定；
- `medial_sound`：目标词中部音段变化；
- `word_final`：词尾音弱化或缺失；
- `pronunciation_variant`：Qwen 对同一拼写生成了不同读法/音节；
- `truncation`：音频切断、词头/词尾不完整；
- `uncertain`：听不出稳定规律。

标签来自对 WAV 的人工检查，不代表 Icefall 解释。所有未唤醒文件都要统计，不能只挑支持既有假设的例子。

## 下一轮验证原则

拿到新唤醒词后，以同一批 Qwen profile、同一 seed/生成轮次和相同 TTS 设置成对生成候选与 hey google；再用相同 Icefall checkpoint、阈值和其余参数得到逐 WAV 结果。报告总命中率、各 profile 命中率、候选减 Google 的配对差与 profile bootstrap 区间，并附漏唤醒标签计数。

若 profile 只有一个，只能报告该 profile 下各词命中比例与生成波动，不能把重复 WAV 当成独立说话人或声称跨音色稳定。不同轮次若合成音频完全重复，也不能算独立样本。快速试验的边界是筛查线，样本不足时结论应为“证据不足”。

## ASR 训练文本与 BPE 因素

这些分数是 KWS 唤醒结果，底层使用 GigaSpeech 训练的原始 ASR 训练模型且没有 KWS 增训。因此结果仍是 KWS 指标，但声学输入、ASR 训练所得模型表示、BPE 子词目标编码及 KWS 解码设置可能共同影响它；不能称为纯声学可辨性测量。

已查看用户提供的 `data/lang_bpe_500/tokens.txt`：直接搜索候选拼写时找到完整词首 piece `▁EVEN`，ID 为 274。这个 ID 是词表编号，不是 EVEN 在 GigaSpeech 中的出现次数；其它词没有完整单 piece 也不代表 OOV，可能会被模型拆成多个正常 piece。需要用配套 `bpe.model` 对完整短语做 SentencePiece 编码，记录 pieces 数、具体序列和是否有 UNK。工程中的 `scripts/analyze_bpe_candidates.py` 可完成该检查。

语料熟悉度必须从与此模型训练对应的 GigaSpeech 正规化转录文本统计精确词频/短语频次；只凭 `tokens.txt` 或 BPE piece 数无法得到语料次数。如果训练文本不可用，应明确标为未知。

分析时并列展示：Qwen WAV 的逐条 KWS 命中、profile/seed 配对、BPE 切分、训练文本词频（若能取得）和未命中音频的听辨标签。若没有逐条转写、token/关键词分数或声学 posterior，只有命中/未命中二值结果，就不能把低命中定量归因于声学、词频或 BPE 中某一项；只能提出后续可验证的假设。

