# 候选词当前结果与分析边界

## 当前 KWS 结果

| 唤醒词 | 用户报告分数 | 相对 hey google |
|---|---:|---:|
| hey google | 0.936 | — |
| hey tesla | 0.895 | -4.1pp |
| hey siri | 0.865 | -7.1pp |
| hey eva | 0.756 | -18.0pp |
| hey even | 0.553 | -38.3pp |
| hey ixio | 0.331 | -60.5pp |
| hey neva | 0.758 | -17.8pp |
| hey kiva | 0.664 | -27.2pp |

这些是用户提供的 Icefall KWS 唤醒结果。当前 KWS 使用 GigaSpeech 原始 ASR 训练模型，没有进行 KWS 增训。你已确认测试 WAV 的词语发音没有问题，因此本实验不再把合成质量或发音变体作为候选难度因素。

目前没有逐词 WAV 数量和逐条结果，分数可以用于排序与选取后续实验对象，不能由此重算置信区间，也不能得出“某音素导致失败”的结论。Eva 与 Neva 结果接近，Kiva 低于 Eva；仅凭词首元音/辅音无法预测 KWS 难易。

## 建议的新词快速验证

1. 用同一 Icefall KWS checkpoint、关键词配置、threshold、keywords-score、解码和音频预处理测试 Google 与候选。
2. 将 KWS 触发 WAV 放进 `results/wake/<candidate>/`，未触发 WAV 放进 `results/no_wake/<candidate>/`。每个候选各有一个子目录，文件名不必改。
3. 运行 `scripts/summarize_kws_folders.py`，自动得到各词分母、命中数、命中率、逐 WAV 区间、与 Google 的百分点差，以及命中/未命中音频的基础波形统计。
4. 低至少 15pp 且区间显示劣化时列为当前配置下高风险；结果模糊、样本不足或 Google 对照参数不同则补测。详细初筛规则见 README。

基础波形统计（时长、RMS、峰值、过零率）只用于指出唤醒组与未唤醒组是否存在可测差异，不证明该差异造成 KWS 失败。当前输入没有 Icefall 连续分数或 posterior，故不能估计声学分数分布或阈值曲线。

## BPE 与 GigaSpeech 语料背景

GigaSpeech 训练语料和 BPE 子词表示可能影响 ASR 训练模型在 KWS 中对词语的建模。应把它们作为模型侧背景与 KWS 命中率并列查看，不把它们称为纯声学难度，也不以此替代实际 KWS 测试。

在提供的 `tokens.txt` 中查到 `▁EVEN` token ID 为 274。整数是 token ID，不是 GigaSpeech 中的词频；其他拼写不在整词 token 中也不代表无法编码，需用配套 `bpe.model` 编码查看实际 pieces。若可取得与模型训练相对应的转录文本，再计算准确词频；否则词频记为未知。

即使某候选命中率较低，同时 pieces 更多或训练文本词频较低，也只能视为待验证关联。要分析声学特征对 KWS 的独立作用，需要 Icefall 导出的逐条连续 KWS 分数或 posterior；仅有触发/未触发标签时，不应做因果归因。
