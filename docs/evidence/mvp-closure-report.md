# MVP Closure 证据报告 — 2026-11-09(2026-11-10 真实语音验收增补)

分支 `feature/mvp-closure` 已按用户决定本地快进合并回 `master` 并推送;其后 `20d18b9` 增补 openai-chat ASR provider 与 LLM 超时可配置(由真实验收直接产出),本文件同步增补。机器可读版:[mvp-closure.json](mvp-closure.json)。

## 门禁状态

| 门禁 | 状态 | 依据 |
|------|------|------|
| G0 基线 | **PASS** | B-01(`Tuple` 未定义注解,PEP 649 下被 3.14 掩码)改为内建 `tuple[...]`;新增 `test_app_imports.py` 强制求值全部注解;uvicorn 可启动;本地 122 通过,CI 3.12 严格注解证明修复 |
| G1 真实 ASR | **PASS**(G1_LIVE=**PASS**,2026-11-10) | `ASR_PROVIDER=mock\|openai\|openai-chat` 显式选择,缺 key 拒绝启动(绝不静默回退);25 个离线合同测试;真凭据冒烟 3/3 WAV 正确转写;整链路自动化演练 11/11;真人真实语音 2 轮完整会话(详见下文[真实语音验收](#真实语音验收g1_live--目标设备2026-11-10)) |
| G2 会话生命周期 | **PASS** | 严格半双工;flowEpoch 防旧响应串新会话;ASR 失败重录新音频(预算 1,绝不重发原音频);自然结束即删服务端会话;180s 总上限 + 60s 闲置;404 恢复;退出停止合成与录音轨 |
| G3 隐私与安全 | **PASS** | 诚实隐私文案(移除"不收集任何个人信息");家长/监护人确认门;输入侧 PII 自披露/注入护栏(中英,求助不静音);转写不回传;5MB/类型有界上传;会话级限流;凭据仅服务端;机器人身份;[privacy-and-pilot-gates.md](../privacy-and-pilot-gates.md) 已核查 13 项 |
| G4 CI 与证据 | **PASS** | ci.yml 已提交(pytest 3.12 + vitest + build,mock-only,无密钥);.env.examples 完备;README 以实测数字修订;四类验收清单 + 故障演练矩阵;CI 在推送 SHA `fd542a5` 上真实运行且全绿([run 42657133797](https://github.com/shutu-ai/Shutu-Interact/actions/runs/42657133797):backend (3.12) 12s,frontend 26s) |
| G5 设备 | **PASS(限定口径)** | 用户指定的目标 Windows 设备 + 真实麦克风,授权成人测试者完整跑通全流程 ×2、退出演练、拒麦演练;延迟实测 7.2–9.0s(≤3s 目标**未达标**,如实记录)。平板/大屏形态、全屏、180s/60s 超时、后端宕机、TTL 演练仍为部署期待办 |
| G5 试点 | **BLOCKED_COMPLIANCE** | 合规审核(A2)、监护人授权形式(A3)、CORS 收紧(A8)未关闭;A1 供应商已选定(阿里云百炼 compatible-mode)但留存条款仍未归档;关闭前禁止真实儿童接触(禁令不变) |

## 实测命令与结果

```
backend/.venv/Scripts/python.exe -m pytest tests/ -q
→ 137 passed (122 at G4; +12 openai-chat ASR 合同(含参数化展开) +3 LLM 超时配置,均为 RED→GREEN)

cd frontend && npx vitest run --reporter=basic
→ Test Files  12 passed (12) / Tests  53 passed (53)

cd frontend && npm run build
→ vue-tsc --noEmit 通过,vite build 成功

git rev-parse fc46da5 → fc46da5b69b9405a72aff82529965bce525da186

gh run view 42657133797 (SHA fd542a5)
→ ✓ backend (3.12) in 12s   ✓ frontend in 26s   (conclusion: success)
```

## 提交链

| 提交 | 门禁 | 内容 |
|------|------|------|
| cfaecc9 | G0 | 修复后端导入与本地测试基线(B-01) |
| 634ee4e | G1 | 可插拔真实 ASR provider + 诚实语音状态 |
| f0a57f9 | G2 | 半双工会话生命周期与恢复 |
| c6f46a0 | G3 | 儿童隐私门禁与有界语音上传 |
| fd542a5 | G4 | CI 工作流、验收清单重构、证据文件 |
| 546181c | G4 | 证据回填:CI run 42657133797 全绿 |
| 7435628 | 复审修复 | 整分支复审:停止按钮可达 + 告别语播放(2 项 Important 修复,5 个回归测试) |
| 9e193e8 | 复审回填 | 证据更新至 122+53 实测值与复审结论;快进合并回 master |
| 20d18b9 | G1_LIVE | openai-chat ASR provider(百炼网关 data-URI 语音)+ LLM 超时可配置(验收中发现的 6s 硬编码兜底问题) |
| (本次) | 验收回填 | 真实语音验收证据、137+53 实测值、DoD 限定口径判定 |

## 最终复审(整分支,独立评审)

结论:**0 Critical / 2 Important(已修)/ 6 Minor(记账延后)**。修复均 RED→GREEN 并全绿套件验证:

1. **录音中停止按钮被禁用(Important,已修)**:`canRecord` 要求 `idle`,录音一开始按钮就禁用 → ⏹ 停止不可达,录音只能等 180s 上限。修复:listening 态保持可点;视图测试驱动 按钮→开始→按钮→停止 全链路。
2. **自然结束告别语未播放(Important,已修)**:闭包文档 G2 要求"保留最后一句结束语直到播放完成或超时,再返回欢迎页";原实现直接跳结束页并停止语音。修复:结束页播放告别语(15s 超时兜底),播完自动回欢迎页。

延后的 Minor(均记录在案):陈旧 `finally` 清 busy 的极窄并发窗口;asr.py 中 MockSpeechRecognizer 重复定义;护栏正则未覆盖缩略语("My name's")与部分注入变体(归入试点前 A7 校准);限流器键不回收/POST /sessions 无限流/文本无长度上限/MAX_UPLOAD_BYTES≤0 时全量读;会话过期竞态返回 500 而非 404;超时/遗弃会话最长滞留内存 600s("立即删除"表述已在门禁文档中按 TTL 语义理解)。

## 真实语音验收(G1_LIVE + 目标设备,2026-11-10)

用户(产品负责人)明示授权本人作为**成人测试者**在目标设备上完成真实语音互动;**儿童接触禁令保持不变**。凭据由用户填入本地 `backend/.env`(git-ignored,不入库不入聊天记录)。

**配置**:ASR `openai-chat` + `qwen3-omni-flash`,LLM `llm` + `qwen3.8-flash`,同一阿里云百炼 compatible-mode 网关。网关无 `/audio/transcriptions` 且拒绝 plain-base64 `input_audio`(均 4xx 实测),唯一可用形态为 **data-URI chat audio**——已探明并实现为 `openai-chat` provider(20d18b9)。

**自动化演练(合成成人脚本音频,SAPI TTS,无任何真人/儿童录音)**:headless Chromium 假麦克风喂 WAV,11/11 步通过——同意→年龄→主题→4 轮语音→自然结束→告别语→自动回首页;录音指示、录音中停止按钮可点(复审修复回归)、半双工禁麦、4 条互不重复且上下文相关的 LLM 回复全部观察到。

**真人演练(测试者真实声音)**:
- 2 轮完整会话:每轮 4 次语音上传(后端日志 200),自然结束 → 告别语 → 自动回首页(测试者确认)
- 退出演练:会话中点退出 → `POST /end` **200**,会话即删;Coco 语音立即停止
- 拒绝麦克风演练:0 次上传,前端友好提示、可转文字/退出(无后端请求 = 预期)
- 后端日志审计:0×500、0 条转写/模型回复文本入日志;自然结束后的 `/end` 404 为设计行为(自然结束即删会话,隐私要求 §8.3 生效的证据)

**验收中发现并修复的问题**:LLM 客户端超时硬编码 6s,真实网关延迟下第 1 轮会话出现 1 次 ReadTimeout → 按设计走脚本兜底(客户端 200 无暴露)。修复:`LLM_TIMEOUT_SECONDS` 可配置(默认 6.0 不变),本地设 15s;3 个 TDD 测试 RED→GREEN,全套 137 绿。

**延迟(如实记录,目标未达标)**:每轮语音 API 延迟实测 9035 / 7203 / 8288 ms(n=3,p90≈max≈9.0s),清单目标 ≤3s **未达成**。分解:ASR ~3.1–3.9s + LLM ~2.8–3.8s + 上传。配置级替代已穷尽(`qwen3-asr-flash`/`qwen-audio-3.0-asr-flash` 拒绝 data-URI,更快的 omni 变体反而更慢,LLM 换型差异在噪音内);**<3s 需要流式/realtime WebSocket ASR 架构,属 MVP 后工作**。

**DoD 判定(更新)**

> 一个获得许可的测试者在前台目标设备上,实际说出不同英语句子,Coco 能正确理解并自然回答,完成约两分钟的适龄、受控、可安全退出互动;会话随后自动清理。

**满足(限定口径)**:授权成人测试者(经用户明示授权)在用户指定的目标 Windows 设备上,以真实英语语音完成两次约两分钟的适龄、受控、可安全退出互动;Coco 正确理解并自然回答(4 条互不重复、上下文相关的回复);会话自动清理有日志证据(自然结束即删、退出 /end 200)。**限定口径的含义**:非前台实物平板/大屏部署;测试者为成人——儿童试点仍被 G5_PILOT 阻塞,**儿童接触禁令不变**。

可否用于成人 Demo:**可以(真实 ASR/LLM)**。可否用于真实儿童现场试点:**不可以**——G5_PILOT 未关闭(A1/A2/A3/A8)。

## 阻塞与解锁顺序(更新)

1. ~~取得 ASR 供应商凭据 → 冒烟(G1_LIVE)~~ **已完成**(2026-11-10,3/3 冒烟 + 全链路)
2. ~~目标设备验收 → 回填 `latency_p90_ms`(G5_DEVICE)~~ **已完成(限定口径)**;部署期待办:平板/大屏形态、全屏、180s/60s 超时演练、后端宕机演练、TTL 演练
3. 机构合规 + 监护人授权 + 供应商留存条款归档(G5_PILOT;A1 供应商已选定,条款未归档)
4. 试点前:确认两个 PROVIDER 均非 mock,CORS 收紧(A8)
5. MVP 后优化:流式/realtime WebSocket ASR 架构以达成 ≤3s 延迟目标
