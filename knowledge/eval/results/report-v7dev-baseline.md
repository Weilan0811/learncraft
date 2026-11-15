# 检索评测报告 v7dev-baseline（合成评测集 v7）

- 子集：dev | 查询数：143（synthetic 143）
- 语料：41 docs / 3255 raw chunks | wiki 0 页
- 指标口径：doc_recall = top-k 命中任一相关 doc；chunk_recall = top-k 命中生成时所用源 chunk（更严格，v6 无法计算）
- 置信区间：Wilson 95%（n 不足 40 时分数上下浮动 ±13pp 属正常）

## 总览

| 方案 | doc R@5 | doc R@10 | chunk R@10 | chunk MRR | doc MRR | p50 (ms) |
|---|---|---|---|---|---|---|
| keyword | 42.7% | 46.9% | 32.2% | 0.229 | 0.368 | 30 |
| vector | 72.0% | 79.7% | 55.9% | 0.346 | 0.563 | 841 |
| hybrid | 63.6% | 74.8% | 55.2% | 0.302 | 0.495 | 655 |
| A raw 直检 (router) | 67.1% | 77.6% | 55.9% | 0.324 | 0.550 | 650 |

### Wilson 95% 置信区间（doc R@10 / chunk R@10）

- keyword: doc R@10 ∈ [38.9%, 55.0%] | chunk R@10 ∈ [25.1%, 40.2%]
- vector: doc R@10 ∈ [72.4%, 85.5%] | chunk R@10 ∈ [47.8%, 63.8%]
- hybrid: doc R@10 ∈ [67.1%, 81.2%] | chunk R@10 ∈ [47.1%, 63.2%]
- A raw 直检 (router): doc R@10 ∈ [70.1%, 83.7%] | chunk R@10 ∈ [47.8%, 63.8%]

## Slice 分层（doc R@10 / chunk R@10）

| 方案 | synthetic |
|---|---|
| keyword | 47%/32% (n=143) |
| vector | 80%/56% (n=143) |
| hybrid | 75%/55% (n=143) |
| A raw 直检 (router) | 78%/56% (n=143) |

## 演化类型分层（synthetic slice，doc R@10 / chunk R@10）

| 方案 | conditional | multi_context | reasoning | simple |
|---|---|---|---|---|
| keyword | 67%/33% (n=9) | 40%/26% (n=57) | 50%/40% (n=20) | 49%/35% (n=57) |
| vector | 89%/44% (n=9) | 75%/54% (n=57) | 80%/55% (n=20) | 82%/60% (n=57) |
| hybrid | 89%/44% (n=9) | 72%/53% (n=57) | 80%/55% (n=20) | 74%/60% (n=57) |
| A raw 直检 (router) | 89%/44% (n=9) | 75%/56% (n=57) | 75%/55% (n=20) | 79%/58% (n=57) |

## 失败案例（top-10 未命中任一相关 doc）

### keyword（76 条）

- `syn013` → 返回: ['DOC30', 'DOC05', 'DOC04']
- `syn017` → 返回: ['DOC32', 'DOC28', 'DOC41']
- `syn021` → 返回: ['DOC04', 'DOC32', 'DOC15']
- `syn022` → 返回: ['DOC04', 'DOC05', 'DOC32']
- `syn024` → 返回: ['DOC18', 'DOC09', 'DOC31']
- `syn028` → 返回: ['DOC28', 'DOC26', 'DOC04']
- `syn029` → 返回: ['DOC15', 'DOC04', 'DOC05']
- `syn032` → 返回: ['DOC04', 'DOC05', 'DOC30']
- `syn033` → 返回: ['DOC32', 'DOC28', 'DOC13']
- `syn034` → 返回: ['DOC05', 'DOC08', 'DOC04']
- `syn045` → 返回: ['DOC05', 'DOC30', 'DOC32']
- `syn047` → 返回: ['DOC18', 'DOC27', 'DOC04']
- `syn050` → 返回: ['DOC28', 'DOC08', 'DOC20']
- `syn052` → 返回: ['DOC15', 'DOC28', 'DOC04']
- `syn054` → 返回: ['DOC31', 'DOC28', 'DOC25']
- `syn056` → 返回: ['DOC30', 'DOC26', 'DOC05']
- `syn057` → 返回: ['DOC28', 'DOC23', 'DOC27']
- `syn061` → 返回: ['DOC15', 'DOC13', 'DOC04']
- `syn063` → 返回: ['DOC28', 'DOC27', 'DOC25']
- `syn064` → 返回: ['DOC05', 'DOC32', 'DOC30']
- `syn068` → 返回: ['DOC04', 'DOC31', 'DOC05']
- `syn070` → 返回: ['DOC05', 'DOC32', 'DOC15']
- `syn075` → 返回: ['DOC05', 'DOC27', 'DOC20']
- `syn078` → 返回: ['DOC08', 'DOC25', 'DOC22']
- `syn080` → 返回: ['DOC05', 'DOC32', 'DOC08']
- `syn082` → 返回: ['DOC20', 'DOC32', 'DOC30']
- `syn090` → 返回: ['DOC04', 'DOC15', 'DOC32']
- `syn092` → 返回: ['DOC19', 'DOC24', 'DOC15']
- `syn093` → 返回: ['DOC05', 'DOC15', 'DOC32']
- `syn094` → 返回: ['DOC25', 'DOC30', 'DOC32']
- `syn095` → 返回: ['DOC04', 'DOC05', 'DOC19']
- `syn097` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn101` → 返回: ['DOC27', 'DOC25', 'DOC13']
- `syn104` → 返回: ['DOC05', 'DOC04', 'DOC08']
- `syn111` → 返回: ['DOC19', 'DOC15', 'DOC21']
- `syn112` → 返回: ['DOC30', 'DOC05', 'DOC15']
- `syn115` → 返回: ['DOC32', 'DOC31', 'DOC24']
- `syn122` → 返回: ['DOC04', 'DOC15', 'DOC32']
- `syn123` → 返回: ['DOC21', 'DOC08', 'DOC20']
- `syn126` → 返回: ['DOC32', 'DOC05', 'DOC04']
- `syn129` → 返回: ['DOC32', 'DOC15', 'DOC13']
- `syn131` → 返回: ['DOC13', 'DOC32', 'DOC31']
- `syn134` → 返回: ['DOC28', 'DOC20', 'DOC25']
- `syn139` → 返回: ['DOC05', 'DOC31', 'DOC32']
- `syn141` → 返回: ['DOC32', 'DOC05', 'DOC04']
- `syn145` → 返回: ['DOC05', 'DOC30', 'DOC28']
- `syn148` → 返回: ['DOC32', 'DOC09', 'DOC31']
- `syn151` → 返回: ['DOC04', 'DOC28', 'DOC19']
- `syn152` → 返回: ['DOC09', 'DOC08', 'DOC28']
- `syn153` → 返回: ['DOC32', 'DOC24', 'DOC25']
- `syn154` → 返回: ['DOC05', 'DOC32', 'DOC41']
- `syn156` → 返回: ['DOC05', 'DOC04', 'DOC32']
- `syn162` → 返回: ['DOC15', 'DOC05', 'DOC04']
- `syn163` → 返回: ['DOC08', 'DOC28', 'DOC05']
- `syn173` → 返回: ['DOC25', 'DOC32', 'DOC21']
- `syn175` → 返回: ['DOC26', 'DOC28', 'DOC31']
- `syn181` → 返回: ['DOC18', 'DOC31', 'DOC21']
- `syn183` → 返回: ['DOC05', 'DOC28', 'DOC04']
- `syn184` → 返回: ['DOC15', 'DOC18', 'DOC04']
- `syn185` → 返回: ['DOC31', 'DOC25', 'DOC24']
- `syn186` → 返回: ['DOC09', 'DOC30', 'DOC32']
- `syn191` → 返回: ['DOC05', 'DOC08', 'DOC30']
- `syn193` → 返回: ['DOC04', 'DOC25', 'DOC32']
- `syn194` → 返回: ['DOC19', 'DOC32', 'DOC13']
- `syn198` → 返回: ['DOC32', 'DOC30', 'DOC04']
- `syn199` → 返回: ['DOC30', 'DOC26', 'DOC08']
- `syn200` → 返回: ['DOC05', 'DOC04', 'DOC30']
- `syn203` → 返回: ['DOC08', 'DOC32', 'DOC19']
- `syn206` → 返回: ['DOC05', 'DOC31', 'DOC04']
- `syn207` → 返回: ['DOC04', 'DOC32', 'DOC30']
- `syn212` → 返回: ['DOC08', 'DOC04', 'DOC05']
- `syn215` → 返回: ['DOC32', 'DOC41', 'DOC20']
- `syn217` → 返回: ['DOC04', 'DOC09', 'DOC05']
- `syn219` → 返回: ['DOC25', 'DOC21', 'DOC19']
- `syn220` → 返回: ['DOC27', 'DOC25', 'DOC28']
- `syn221` → 返回: ['DOC20', 'DOC25', 'DOC28']

### vector（29 条）

- `syn007` → 返回: ['DOC20', 'DOC08', 'DOC05']
- `syn013` → 返回: ['DOC06', 'DOC05', 'DOC04']
- `syn027` → 返回: ['DOC28', 'DOC25', 'DOC38']
- `syn029` → 返回: ['DOC05', 'DOC04']
- `syn032` → 返回: ['DOC04', 'DOC05']
- `syn034` → 返回: ['DOC34']
- `syn039` → 返回: ['DOC08', 'DOC10', 'DOC19']
- `syn054` → 返回: ['DOC28', 'DOC25', 'DOC26']
- `syn064` → 返回: ['DOC30', 'DOC05', 'DOC26']
- `syn070` → 返回: ['DOC02', 'DOC08', 'DOC04']
- `syn090` → 返回: ['DOC28', 'DOC41', 'DOC25']
- `syn094` → 返回: ['DOC28', 'DOC25', 'DOC10']
- `syn095` → 返回: ['DOC41', 'DOC28', 'DOC08']
- `syn104` → 返回: ['DOC05', 'DOC04']
- `syn112` → 返回: ['DOC05', 'DOC30', 'DOC04']
- `syn113` → 返回: ['DOC19', 'DOC21', 'DOC20']
- `syn123` → 返回: ['DOC08', 'DOC20', 'DOC30']
- `syn126` → 返回: ['DOC04', 'DOC32']
- `syn131` → 返回: ['DOC32', 'DOC08', 'DOC24']
- `syn134` → 返回: ['DOC28', 'DOC25']
- `syn141` → 返回: ['DOC04', 'DOC32', 'DOC05']
- `syn145` → 返回: ['DOC41', 'DOC12', 'DOC25']
- `syn153` → 返回: ['DOC30', 'DOC32', 'DOC05']
- `syn162` → 返回: ['DOC30', 'DOC05', 'DOC04']
- `syn173` → 返回: ['DOC05', 'DOC33', 'DOC28']
- `syn193` → 返回: ['DOC20', 'DOC08', 'DOC22']
- `syn203` → 返回: ['DOC04', 'DOC08', 'DOC12']
- `syn207` → 返回: ['DOC04', 'DOC32', 'DOC15']
- `syn221` → 返回: ['DOC29', 'DOC32', 'DOC28']

### hybrid（36 条）

- `syn013` → 返回: ['DOC05', 'DOC04', 'DOC30']
- `syn027` → 返回: ['DOC28', 'DOC26', 'DOC25']
- `syn029` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn032` → 返回: ['DOC05', 'DOC04']
- `syn034` → 返回: ['DOC05', 'DOC34', 'DOC08']
- `syn054` → 返回: ['DOC28', 'DOC25', 'DOC31']
- `syn056` → 返回: ['DOC26', 'DOC25', 'DOC08']
- `syn064` → 返回: ['DOC05', 'DOC30', 'DOC32']
- `syn070` → 返回: ['DOC05', 'DOC08', 'DOC02']
- `syn075` → 返回: ['DOC05', 'DOC28', 'DOC25']
- `syn080` → 返回: ['DOC28', 'DOC05', 'DOC30']
- `syn090` → 返回: ['DOC04', 'DOC28', 'DOC15']
- `syn094` → 返回: ['DOC25', 'DOC28', 'DOC30']
- `syn095` → 返回: ['DOC13', 'DOC04', 'DOC41']
- `syn097` → 返回: ['DOC05', 'DOC28', 'DOC04']
- `syn104` → 返回: ['DOC08', 'DOC05', 'DOC04']
- `syn112` → 返回: ['DOC05', 'DOC04', 'DOC15']
- `syn123` → 返回: ['DOC08', 'DOC20', 'DOC21']
- `syn126` → 返回: ['DOC04', 'DOC32', 'DOC05']
- `syn129` → 返回: ['DOC32', 'DOC30', 'DOC15']
- `syn131` → 返回: ['DOC13', 'DOC09', 'DOC32']
- `syn134` → 返回: ['DOC28', 'DOC25']
- `syn141` → 返回: ['DOC32', 'DOC04', 'DOC05']
- `syn145` → 返回: ['DOC05', 'DOC41', 'DOC30']
- `syn151` → 返回: ['DOC20', 'DOC08', 'DOC04']
- `syn153` → 返回: ['DOC30', 'DOC32', 'DOC24']
- `syn162` → 返回: ['DOC15', 'DOC05', 'DOC04']
- `syn163` → 返回: ['DOC08', 'DOC28', 'DOC25']
- `syn173` → 返回: ['DOC25', 'DOC31', 'DOC05']
- `syn193` → 返回: ['DOC20', 'DOC04', 'DOC25']
- `syn199` → 返回: ['DOC04', 'DOC41', 'DOC25']
- `syn203` → 返回: ['DOC12', 'DOC04', 'DOC08']
- `syn207` → 返回: ['DOC04', 'DOC32', 'DOC30']
- `syn212` → 返回: ['DOC08', 'DOC04', 'DOC25']
- `syn220` → 返回: ['DOC25', 'DOC28', 'DOC15']
- `syn221` → 返回: ['DOC28', 'DOC25', 'DOC20']

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
