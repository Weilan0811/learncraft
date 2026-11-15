# 检索评测报告 v7dev（合成评测集 v7）

- 子集：dev | 查询数：143（synthetic 143）
- 语料：41 docs / 3255 raw chunks | wiki 50 页
- 指标口径：doc_recall = top-k 命中任一相关 doc；chunk_recall = top-k 命中生成时所用源 chunk（更严格，v6 无法计算）
- 置信区间：Wilson 95%（n 不足 40 时分数上下浮动 ±13pp 属正常）

## 总览

| 方案 | doc R@5 | doc R@10 | chunk R@10 | chunk MRR | doc MRR | p50 (ms) |
|---|---|---|---|---|---|---|
| A raw 直检 (router) | 67.1% | 77.6% | 55.9% | 0.324 | 0.550 | 557 |
| B wiki 展开·轮转 | 54.5% | 69.2% | 7.7% | 0.036 | 0.337 | 298 |
| B wiki 展开·池内重排 | 55.9% | 58.0% | 42.0% | 0.272 | 0.447 | 701 |
| C fused·RRF (v6 形态) | 64.3% | 76.2% | 50.3% | 0.275 | 0.528 | 608 |
| C fused·top10∪top10 | 67.1% | 77.6% | 55.9% | 0.324 | 0.550 | 607 |
| C fused·大池漏斗 (raw50+wiki) | 67.1% | 76.2% | 49.7% | 0.216 | 0.480 | 608 |
| C fused·配额均分 (5+5) | 62.9% | 76.2% | 50.3% | 0.282 | 0.536 | 607 |

### Wilson 95% 置信区间（doc R@10 / chunk R@10）

- A raw 直检 (router): doc R@10 ∈ [70.1%, 83.7%] | chunk R@10 ∈ [47.8%, 63.8%]
- B wiki 展开·轮转: doc R@10 ∈ [61.2%, 76.2%] | chunk R@10 ∈ [4.3%, 13.2%]
- B wiki 展开·池内重排: doc R@10 ∈ [49.8%, 65.8%] | chunk R@10 ∈ [34.2%, 50.2%]
- C fused·RRF (v6 形态): doc R@10 ∈ [68.6%, 82.5%] | chunk R@10 ∈ [42.3%, 58.4%]
- C fused·top10∪top10: doc R@10 ∈ [70.1%, 83.7%] | chunk R@10 ∈ [47.8%, 63.8%]
- C fused·大池漏斗 (raw50+wiki): doc R@10 ∈ [68.6%, 82.5%] | chunk R@10 ∈ [41.6%, 57.7%]
- C fused·配额均分 (5+5): doc R@10 ∈ [68.6%, 82.5%] | chunk R@10 ∈ [42.3%, 58.4%]

## Slice 分层（doc R@10 / chunk R@10）

| 方案 | synthetic |
|---|---|
| A raw 直检 (router) | 78%/56% (n=143) |
| B wiki 展开·轮转 | 69%/8% (n=143) |
| B wiki 展开·池内重排 | 58%/42% (n=143) |
| C fused·RRF (v6 形态) | 76%/50% (n=143) |
| C fused·top10∪top10 | 78%/56% (n=143) |
| C fused·大池漏斗 (raw50+wiki) | 76%/50% (n=143) |
| C fused·配额均分 (5+5) | 76%/50% (n=143) |

## 演化类型分层（synthetic slice，doc R@10 / chunk R@10）

| 方案 | conditional | multi_context | reasoning | simple |
|---|---|---|---|---|
| A raw 直检 (router) | 89%/44% (n=9) | 75%/56% (n=57) | 75%/55% (n=20) | 79%/58% (n=57) |
| B wiki 展开·轮转 | 78%/11% (n=9) | 65%/5% (n=57) | 70%/10% (n=20) | 72%/9% (n=57) |
| B wiki 展开·池内重排 | 67%/33% (n=9) | 54%/42% (n=57) | 55%/45% (n=20) | 61%/42% (n=57) |
| C fused·RRF (v6 形态) | 89%/44% (n=9) | 72%/46% (n=57) | 85%/50% (n=20) | 75%/56% (n=57) |
| C fused·top10∪top10 | 89%/44% (n=9) | 75%/56% (n=57) | 75%/55% (n=20) | 79%/58% (n=57) |
| C fused·大池漏斗 (raw50+wiki) | 89%/44% (n=9) | 72%/46% (n=57) | 85%/50% (n=20) | 75%/54% (n=57) |
| C fused·配额均分 (5+5) | 89%/44% (n=9) | 72%/46% (n=57) | 85%/50% (n=20) | 75%/56% (n=57) |

## Citation fidelity（wiki 系臂）

- source_refs：16166 | exact 79.3% + degraded 20.7% = 解析率 100.0% | 硬失败 0

## 失败案例（top-10 未命中任一相关 doc）

### A raw 直检 (router)（32 条）

- `syn007` → 返回: ['DOC08', 'DOC28', 'DOC20']
- `syn013` → 返回: ['DOC05', 'DOC04', 'DOC06']
- `syn027` → 返回: ['DOC28', 'DOC25', 'DOC23']
- `syn029` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn032` → 返回: ['DOC04', 'DOC05']
- `syn034` → 返回: ['DOC34']
- `syn039` → 返回: ['DOC19', 'DOC13', 'DOC08']
- `syn054` → 返回: ['DOC28', 'DOC25', 'DOC26']
- `syn056` → 返回: ['DOC26', 'DOC25', 'DOC08']
- `syn064` → 返回: ['DOC05', 'DOC30', 'DOC26']
- `syn070` → 返回: ['DOC08', 'DOC05', 'DOC02']
- `syn090` → 返回: ['DOC28', 'DOC41', 'DOC25']
- `syn094` → 返回: ['DOC25', 'DOC28', 'DOC10']
- `syn095` → 返回: ['DOC13', 'DOC41', 'DOC28']
- `syn104` → 返回: ['DOC05', 'DOC08']
- `syn112` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn113` → 返回: ['DOC19', 'DOC21', 'DOC20']
- `syn123` → 返回: ['DOC08', 'DOC20', 'DOC21']
- `syn126` → 返回: ['DOC04', 'DOC32', 'DOC05']
- `syn131` → 返回: ['DOC09', 'DOC13', 'DOC32']
- `syn134` → 返回: ['DOC28', 'DOC25']
- `syn141` → 返回: ['DOC32', 'DOC04', 'DOC05']
- `syn145` → 返回: ['DOC05', 'DOC41', 'DOC12']
- `syn153` → 返回: ['DOC30', 'DOC32']
- `syn162` → 返回: ['DOC05', 'DOC30', 'DOC15']
- `syn173` → 返回: ['DOC25', 'DOC31', 'DOC05']
- `syn193` → 返回: ['DOC20', 'DOC08', 'DOC22']
- `syn199` → 返回: ['DOC04', 'DOC41', 'DOC25']
- `syn203` → 返回: ['DOC12', 'DOC04', 'DOC08']
- `syn207` → 返回: ['DOC04', 'DOC32', 'DOC15']
- `syn220` → 返回: ['DOC25', 'DOC28', 'DOC15']
- `syn221` → 返回: ['DOC28', 'DOC25', 'DOC29']

### B wiki 展开·轮转（44 条）

- `syn002` → 返回: ['DOC08', 'DOC13', 'DOC30']
- `syn018` → 返回: ['DOC08', 'DOC32', 'DOC13']
- `syn022` → 返回: ['DOC04', 'DOC05', 'DOC32']
- `syn027` → 返回: ['DOC41', 'DOC23', 'DOC13']
- `syn028` → 返回: ['DOC23', 'DOC13', 'DOC32']
- `syn029` → 返回: ['DOC05', 'DOC15', 'DOC04']
- `syn033` → 返回: ['DOC41', 'DOC13', 'DOC28']
- `syn034` → 返回: ['DOC30', 'DOC23', 'DOC25']
- `syn048` → 返回: ['DOC13', 'DOC23', 'DOC22']
- `syn052` → 返回: ['DOC13', 'DOC41', 'DOC30']
- `syn054` → 返回: ['DOC41', 'DOC28', 'DOC25']
- `syn056` → 返回: ['DOC09', 'DOC30', 'DOC13']
- `syn057` → 返回: ['DOC41', 'DOC13', 'DOC23']
- `syn064` → 返回: ['DOC05', 'DOC08', 'DOC41']
- `syn070` → 返回: ['DOC13', 'DOC08', 'DOC31']
- `syn073` → 返回: ['DOC08', 'DOC13', 'DOC05']
- `syn080` → 返回: ['DOC13', 'DOC41', 'DOC30']
- `syn090` → 返回: ['DOC31', 'DOC28', 'DOC13']
- `syn094` → 返回: ['DOC41', 'DOC28', 'DOC13']
- `syn095` → 返回: ['DOC13', 'DOC41', 'DOC08']
- `syn097` → 返回: ['DOC41', 'DOC25', 'DOC30']
- `syn104` → 返回: ['DOC05', 'DOC15', 'DOC04']
- `syn111` → 返回: ['DOC08', 'DOC05', 'DOC30']
- `syn122` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn123` → 返回: ['DOC08', 'DOC13', 'DOC30']
- `syn131` → 返回: ['DOC41', 'DOC13', 'DOC08']
- `syn139` → 返回: ['DOC15', 'DOC17', 'DOC18']
- `syn145` → 返回: ['DOC41', 'DOC13', 'DOC05']
- `syn153` → 返回: ['DOC13', 'DOC32', 'DOC36']
- `syn156` → 返回: ['DOC13', 'DOC08', 'DOC41']
- `syn162` → 返回: ['DOC04', 'DOC13', 'DOC15']
- `syn164` → 返回: ['DOC08', 'DOC20', 'DOC13']
- `syn168` → 返回: ['DOC30', 'DOC08', 'DOC13']
- `syn173` → 返回: ['DOC13', 'DOC31', 'DOC29']
- `syn180` → 返回: ['DOC13', 'DOC30', 'DOC41']
- `syn185` → 返回: ['DOC13', 'DOC41', 'DOC30']
- `syn191` → 返回: ['DOC05', 'DOC13', 'DOC41']
- `syn193` → 返回: ['DOC30', 'DOC13', 'DOC18']
- `syn199` → 返回: ['DOC41', 'DOC31', 'DOC32']
- `syn207` → 返回: ['DOC04', 'DOC15', 'DOC05']
- `syn212` → 返回: ['DOC41', 'DOC08', 'DOC13']
- `syn215` → 返回: ['DOC41', 'DOC13', 'DOC23']
- `syn219` → 返回: ['DOC13', 'DOC41', 'DOC08']
- `syn221` → 返回: ['DOC13', 'DOC41', 'DOC28']

### B wiki 展开·池内重排（60 条）

- `syn002` → 返回: ['DOC08', 'DOC09', 'DOC31']
- `syn007` → 返回: ['DOC08', 'DOC09', 'DOC05']
- `syn010` → 返回: ['DOC34', 'DOC22', 'DOC32']
- `syn013` → 返回: ['DOC06', 'DOC14', 'DOC19']
- `syn018` → 返回: ['DOC21', 'DOC30', 'DOC31']
- `syn022` → 返回: ['DOC04', 'DOC15']
- `syn027` → 返回: ['DOC28', 'DOC23', 'DOC26']
- `syn028` → 返回: ['DOC26', 'DOC28']
- `syn029` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn032` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn033` → 返回: ['DOC26', 'DOC28', 'DOC41']
- `syn034` → 返回: ['DOC34']
- `syn039` → 返回: ['DOC08', 'DOC21', 'DOC13']
- `syn048` → 返回: ['DOC22', 'DOC23', 'DOC08']
- `syn052` → 返回: ['DOC41', 'DOC30', 'DOC27']
- `syn054` → 返回: ['DOC28', 'DOC26', 'DOC41']
- `syn056` → 返回: ['DOC26', 'DOC08']
- `syn057` → 返回: ['DOC40', 'DOC23', 'DOC28']
- `syn064` → 返回: ['DOC26', 'DOC05', 'DOC08']
- `syn070` → 返回: ['DOC02', 'DOC04', 'DOC15']
- `syn073` → 返回: ['DOC12']
- `syn080` → 返回: ['DOC41', 'DOC13', 'DOC37']
- `syn090` → 返回: ['DOC28', 'DOC41']
- `syn094` → 返回: ['DOC28', 'DOC41', 'DOC30']
- `syn095` → 返回: ['DOC41', 'DOC28', 'DOC08']
- `syn097` → 返回: ['DOC28']
- `syn104` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn111` → 返回: ['DOC08', 'DOC30']
- `syn112` → 返回: ['DOC05', 'DOC15', 'DOC04']
- `syn113` → 返回: ['DOC19', 'DOC21', 'DOC20']
- `syn118` → 返回: ['DOC04', 'DOC05', 'DOC15']
- `syn122` → 返回: ['DOC15', 'DOC04']
- `syn123` → 返回: ['DOC08', 'DOC20', 'DOC30']
- `syn126` → 返回: ['DOC04', 'DOC32', 'DOC30']
- `syn127` → 返回: ['DOC02', 'DOC20', 'DOC08']
- `syn131` → 返回: ['DOC08', 'DOC13', 'DOC26']
- `syn134` → 返回: ['DOC28', 'DOC26', 'DOC16']
- `syn139` → 返回: ['DOC17', 'DOC15', 'DOC29']
- `syn145` → 返回: ['DOC12', 'DOC13', 'DOC08']
- `syn146` → 返回: ['DOC15', 'DOC32', 'DOC04']
- `syn153` → 返回: ['DOC08', 'DOC32', 'DOC17']
- `syn156` → 返回: ['DOC05', 'DOC15', 'DOC08']
- `syn162` → 返回: ['DOC15', 'DOC04', 'DOC21']
- `syn164` → 返回: ['DOC20', 'DOC18', 'DOC08']
- `syn168` → 返回: ['DOC30', 'DOC08']
- `syn173` → 返回: ['DOC31', 'DOC41', 'DOC29']
- `syn175` → 返回: ['DOC26', 'DOC28', 'DOC41']
- `syn179` → 返回: ['DOC28', 'DOC26']
- `syn180` → 返回: ['DOC08', 'DOC21', 'DOC30']
- `syn185` → 返回: ['DOC28', 'DOC08', 'DOC30']
- `syn186` → 返回: ['DOC32', 'DOC30']
- `syn191` → 返回: ['DOC05', 'DOC30', 'DOC13']
- `syn193` → 返回: ['DOC08', 'DOC22', 'DOC30']
- `syn199` → 返回: ['DOC41', 'DOC27', 'DOC23']
- `syn203` → 返回: ['DOC08', 'DOC12']
- `syn207` → 返回: ['DOC32', 'DOC15', 'DOC04']
- `syn212` → 返回: ['DOC08', 'DOC28', 'DOC33']
- `syn215` → 返回: ['DOC23', 'DOC41', 'DOC40']
- `syn219` → 返回: ['DOC30', 'DOC08']
- `syn221` → 返回: ['DOC28', 'DOC27', 'DOC26']

### C fused·RRF (v6 形态)（34 条）

- `syn013` → 返回: ['DOC05', 'DOC13', 'DOC04']
- `syn027` → 返回: ['DOC23', 'DOC28', 'DOC41']
- `syn029` → 返回: ['DOC05', 'DOC15', 'DOC04']
- `syn032` → 返回: ['DOC05', 'DOC04', 'DOC30']
- `syn034` → 返回: ['DOC34', 'DOC30', 'DOC23']
- `syn039` → 返回: ['DOC19', 'DOC08', 'DOC13']
- `syn054` → 返回: ['DOC28', 'DOC41', 'DOC25']
- `syn056` → 返回: ['DOC26', 'DOC09', 'DOC25']
- `syn064` → 返回: ['DOC05', 'DOC30', 'DOC08']
- `syn070` → 返回: ['DOC05', 'DOC08', 'DOC13']
- `syn075` → 返回: ['DOC05', 'DOC08', 'DOC28']
- `syn080` → 返回: ['DOC28', 'DOC13', 'DOC30']
- `syn090` → 返回: ['DOC28', 'DOC41', 'DOC31']
- `syn094` → 返回: ['DOC25', 'DOC41', 'DOC28']
- `syn095` → 返回: ['DOC13', 'DOC41', 'DOC08']
- `syn097` → 返回: ['DOC28', 'DOC41', 'DOC25']
- `syn104` → 返回: ['DOC05', 'DOC15', 'DOC04']
- `syn122` → 返回: ['DOC04', 'DOC05', 'DOC15']
- `syn123` → 返回: ['DOC08', 'DOC20', 'DOC13']
- `syn131` → 返回: ['DOC09', 'DOC41', 'DOC13']
- `syn141` → 返回: ['DOC32', 'DOC31', 'DOC04']
- `syn145` → 返回: ['DOC41', 'DOC05', 'DOC13']
- `syn151` → 返回: ['DOC20', 'DOC41', 'DOC08']
- `syn153` → 返回: ['DOC30', 'DOC13', 'DOC32']
- `syn162` → 返回: ['DOC05', 'DOC04', 'DOC30']
- `syn163` → 返回: ['DOC28', 'DOC08', 'DOC25']
- `syn173` → 返回: ['DOC25', 'DOC13', 'DOC31']
- `syn191` → 返回: ['DOC05', 'DOC13', 'DOC41']
- `syn193` → 返回: ['DOC20', 'DOC30', 'DOC13']
- `syn199` → 返回: ['DOC41', 'DOC04', 'DOC31']
- `syn203` → 返回: ['DOC12', 'DOC08', 'DOC04']
- `syn207` → 返回: ['DOC04', 'DOC15', 'DOC05']
- `syn212` → 返回: ['DOC08', 'DOC41', 'DOC25']
- `syn221` → 返回: ['DOC28', 'DOC13', 'DOC41']

### C fused·top10∪top10（32 条）

- `syn007` → 返回: ['DOC08', 'DOC28', 'DOC20']
- `syn013` → 返回: ['DOC05', 'DOC04', 'DOC06']
- `syn027` → 返回: ['DOC28', 'DOC25', 'DOC23']
- `syn029` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn032` → 返回: ['DOC04', 'DOC05']
- `syn034` → 返回: ['DOC34']
- `syn039` → 返回: ['DOC19', 'DOC13', 'DOC08']
- `syn054` → 返回: ['DOC28', 'DOC25', 'DOC26']
- `syn056` → 返回: ['DOC26', 'DOC25', 'DOC08']
- `syn064` → 返回: ['DOC05', 'DOC30', 'DOC26']
- `syn070` → 返回: ['DOC08', 'DOC05', 'DOC02']
- `syn090` → 返回: ['DOC28', 'DOC41', 'DOC25']
- `syn094` → 返回: ['DOC25', 'DOC28', 'DOC10']
- `syn095` → 返回: ['DOC13', 'DOC41', 'DOC28']
- `syn104` → 返回: ['DOC05', 'DOC08']
- `syn112` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn113` → 返回: ['DOC19', 'DOC21', 'DOC20']
- `syn123` → 返回: ['DOC08', 'DOC20', 'DOC21']
- `syn126` → 返回: ['DOC04', 'DOC32', 'DOC05']
- `syn131` → 返回: ['DOC09', 'DOC13', 'DOC32']
- `syn134` → 返回: ['DOC28', 'DOC25']
- `syn141` → 返回: ['DOC32', 'DOC04', 'DOC05']
- `syn145` → 返回: ['DOC05', 'DOC41', 'DOC12']
- `syn153` → 返回: ['DOC30', 'DOC32']
- `syn162` → 返回: ['DOC05', 'DOC30', 'DOC15']
- `syn173` → 返回: ['DOC25', 'DOC31', 'DOC05']
- `syn193` → 返回: ['DOC20', 'DOC08', 'DOC22']
- `syn199` → 返回: ['DOC04', 'DOC41', 'DOC25']
- `syn203` → 返回: ['DOC12', 'DOC04', 'DOC08']
- `syn207` → 返回: ['DOC04', 'DOC32', 'DOC15']
- `syn220` → 返回: ['DOC25', 'DOC28', 'DOC15']
- `syn221` → 返回: ['DOC28', 'DOC25', 'DOC29']

### C fused·大池漏斗 (raw50+wiki)（34 条）

- `syn013` → 返回: ['DOC05', 'DOC13', 'DOC04']
- `syn027` → 返回: ['DOC23', 'DOC28', 'DOC25']
- `syn029` → 返回: ['DOC04', 'DOC05', 'DOC15']
- `syn032` → 返回: ['DOC05', 'DOC04', 'DOC30']
- `syn034` → 返回: ['DOC34', 'DOC30', 'DOC23']
- `syn054` → 返回: ['DOC28', 'DOC05', 'DOC41']
- `syn056` → 返回: ['DOC26', 'DOC09', 'DOC25']
- `syn057` → 返回: ['DOC23', 'DOC41', 'DOC28']
- `syn064` → 返回: ['DOC23', 'DOC05', 'DOC30']
- `syn070` → 返回: ['DOC05', 'DOC08', 'DOC04']
- `syn075` → 返回: ['DOC41', 'DOC22', 'DOC05']
- `syn080` → 返回: ['DOC41', 'DOC32', 'DOC28']
- `syn090` → 返回: ['DOC28', 'DOC41', 'DOC05']
- `syn094` → 返回: ['DOC25', 'DOC41', 'DOC28']
- `syn095` → 返回: ['DOC13', 'DOC41', 'DOC32']
- `syn097` → 返回: ['DOC32', 'DOC28', 'DOC41']
- `syn104` → 返回: ['DOC05', 'DOC15', 'DOC04']
- `syn122` → 返回: ['DOC04', 'DOC05', 'DOC15']
- `syn123` → 返回: ['DOC13', 'DOC08', 'DOC20']
- `syn131` → 返回: ['DOC41', 'DOC09', 'DOC13']
- `syn141` → 返回: ['DOC04', 'DOC05', 'DOC32']
- `syn145` → 返回: ['DOC41', 'DOC05', 'DOC13']
- `syn151` → 返回: ['DOC20', 'DOC41', 'DOC08']
- `syn153` → 返回: ['DOC30', 'DOC13', 'DOC32']
- `syn162` → 返回: ['DOC04', 'DOC05', 'DOC30']
- `syn163` → 返回: ['DOC28', 'DOC05', 'DOC13']
- `syn173` → 返回: ['DOC23', 'DOC25', 'DOC13']
- `syn191` → 返回: ['DOC05', 'DOC13', 'DOC41']
- `syn193` → 返回: ['DOC22', 'DOC41', 'DOC23']
- `syn199` → 返回: ['DOC41', 'DOC23', 'DOC24']
- `syn203` → 返回: ['DOC05', 'DOC12', 'DOC08']
- `syn207` → 返回: ['DOC04', 'DOC15', 'DOC05']
- `syn212` → 返回: ['DOC08', 'DOC41', 'DOC25']
- `syn221` → 返回: ['DOC13', 'DOC26', 'DOC28']

### C fused·配额均分 (5+5)（34 条）

- `syn013` → 返回: ['DOC05', 'DOC13', 'DOC04']
- `syn027` → 返回: ['DOC28', 'DOC41', 'DOC25']
- `syn029` → 返回: ['DOC05', 'DOC15', 'DOC04']
- `syn032` → 返回: ['DOC04', 'DOC05', 'DOC30']
- `syn034` → 返回: ['DOC34', 'DOC30', 'DOC23']
- `syn039` → 返回: ['DOC19', 'DOC08', 'DOC13']
- `syn054` → 返回: ['DOC28', 'DOC41', 'DOC25']
- `syn056` → 返回: ['DOC26', 'DOC09', 'DOC25']
- `syn064` → 返回: ['DOC05', 'DOC30', 'DOC08']
- `syn070` → 返回: ['DOC08', 'DOC13', 'DOC05']
- `syn075` → 返回: ['DOC05', 'DOC08', 'DOC28']
- `syn080` → 返回: ['DOC28', 'DOC13', 'DOC30']
- `syn090` → 返回: ['DOC28', 'DOC31', 'DOC13']
- `syn094` → 返回: ['DOC25', 'DOC41', 'DOC28']
- `syn095` → 返回: ['DOC13', 'DOC41', 'DOC08']
- `syn097` → 返回: ['DOC28', 'DOC41', 'DOC25']
- `syn104` → 返回: ['DOC05', 'DOC15', 'DOC04']
- `syn122` → 返回: ['DOC04', 'DOC05', 'DOC15']
- `syn123` → 返回: ['DOC08', 'DOC20', 'DOC13']
- `syn131` → 返回: ['DOC09', 'DOC41', 'DOC13']
- `syn141` → 返回: ['DOC32', 'DOC31', 'DOC04']
- `syn145` → 返回: ['DOC05', 'DOC41', 'DOC13']
- `syn151` → 返回: ['DOC20', 'DOC41', 'DOC08']
- `syn153` → 返回: ['DOC30', 'DOC13', 'DOC32']
- `syn162` → 返回: ['DOC05', 'DOC04', 'DOC30']
- `syn163` → 返回: ['DOC28', 'DOC08', 'DOC25']
- `syn173` → 返回: ['DOC25', 'DOC13', 'DOC31']
- `syn191` → 返回: ['DOC05', 'DOC13', 'DOC41']
- `syn193` → 返回: ['DOC20', 'DOC30', 'DOC13']
- `syn199` → 返回: ['DOC04', 'DOC41', 'DOC31']
- `syn203` → 返回: ['DOC12', 'DOC08', 'DOC04']
- `syn207` → 返回: ['DOC04', 'DOC15', 'DOC05']
- `syn212` → 返回: ['DOC08', 'DOC41', 'DOC25']
- `syn221` → 返回: ['DOC28', 'DOC13', 'DOC41']
