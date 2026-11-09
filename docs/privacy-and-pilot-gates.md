# 隐私与试点门禁 — Privacy & Pilot Gates

> 状态日期:2026-11-09(MVP Closure G3)。本文档区分**已核查**(代码与测试可证)与**待核查**(需机构/人工/真实环境确认)的事项。任何一项待核查未关闭前,禁止用于真实儿童现场试点。

## 数据流(当前实现)

```
孩子语音 → 浏览器 MediaRecorder(webm)
        → POST /api/sessions/{id}/speech   (大小/类型有界,会话级限流)
        → ASR provider(ASR_PROVIDER 配置;凭据只在服务端 env)
        → 转写文本: 输入侧安全检查;命中即以 "[redacted]" 占位,原文不落内存历史、不回传前端、不进日志
        → 对话引擎(mock 脚本 或 LLM)→ 回复行 → 浏览器 speechSynthesis 播报
        → 会话结束(自然收尾/退出/超时)→ 服务端立即删除会话(转写占位与轮次全部随会话消失)
```

内存会话 + TTL(默认 600s)+ 总时长上限(默认 180s)+ 自然结束即删。无数据库,无持久化文件。

## 已核查(代码与自动化测试可证)

| # | 事项 | 证据 |
|---|------|------|
| 1 | 前端**不使用** localStorage / sessionStorage / cookie / IndexedDB 存任何对话内容 | 全源码 grep 审计(0 命中);状态仅在 Pinia 内存,reset 即清 |
| 2 | 语音上传**有界**:默认 ≤5MB、仅 `audio/*` 类型;超限 413/415 | `test_speech_rejects_oversized_audio` / `test_speech_rejects_non_audio_content_type` |
| 3 | 会话级限流:每分钟默认 12 轮,404/失败轮次也计数(不可被滥用以绕过) | `test_turns_are_rate_limited_per_session`、`backend/app/services/rate_limiter.py` |
| 4 | 转写**最小化**:响应不回传转写文本;命中输入护栏的原文不存储(占位符对齐)、不打印日志 | `test_speech_returns_next_turn_without_echoing_transcript`、`test_guarded_routes`(caplog 断言) |
| 5 | 输入侧 PII 自披露护栏:自报姓名/电话/住址/学校(含中文表述、CN 手机号形态)→ 拦截并脚本化温和改道 | `test_safety_guard.py::SELF_DISCLOSURE_INPUTS`(11 例) |
| 6 | 提示注入护栏(中英)→ 拦截 | `test_safety_guard.py::INJECTION_INPUTS`(5 例) |
| 7 | **求助儿童永不被静音**:"help me / 我怕黑"等不命中任何拦截;拦截路径的回复也是温和鼓励,不是沉默 | `test_safety_guard.py::HELP_SEEKING_INPUTS`(4 例) |
| 8 | 输出侧护栏:PII 提问/暴力/金钱/医疗法律/诱导依赖 → 脚本回退 | `test_safety_guard.py`(既有 24 例 + 上述) |
| 9 | 凭据只在服务端 env(`LLM_API_KEY`/`ASR_API_KEY`);前端代码无任何 key;缺 key 时 llm/openai 模式拒绝启动,绝不静默回退 mock | `test_engine_selection.py`、`test_asr_provider.py` |
| 10 | 会话生命周期:自然结束即删 + 180s 总上限 + 600s TTL;过期/超限 404 | `test_session_cleanup.py`、`test_sessions.py::test_reply_finishes_after_max_turns` |
| 11 | 严格半双工:Coco 说话时麦克风不可开;退出/超时/beforeunload 停止合成与录音轨 | `session.lifecycle.spec.ts`(11 例) |
| 12 | 事件循环不阻塞:语音路由同步化(线程池) | `test_speech_route_runs_in_threadpool` |
| 13 | mock 明确显式选择;生产/试点禁用 mock(README 部署说明) | README §部署说明 6–7 |

## 待核查(需机构/人工/真实环境关闭 — 均为试点前置)

| # | 事项 | 关闭方式 | 阻塞 |
|---|------|----------|------|
| A1 | 真实 ASR provider 的数据留存/训练政策:所选供应商是否留存/使用上传音频,需其 DPA/条款确认;必要时选零留存参数 | 选定供应商后归档条款链接到本文件 | G1_LIVE=BLOCKED_CREDENTIALS |
| A2 | 机构合规审核:未成年人互动的内部审批(法务/负责人) | 机构出具书面批准,附于试点材料 | G5_PILOT=BLOCKED_COMPLIANCE |
| A3 | 监护人授权流程:现场口头同意已有(前端确认门),是否需要书面/电子授权单由机构定 | 机构决定并落文档 | 同上 |
| A4 | 前台网络与 HTTPS:getUserMedia 需安全上下文;需内网证书 + 域名 | 部署时配置并记录 | G5_DEVICE=BLOCKED_DEVICE |
| A5 | 真实设备验收:目标平板/大屏 + 真实麦克风音质、延迟 p90、误识别率 | 按 docs/acceptance-checklist.md 现场执行 | G5_DEVICE=BLOCKED_DEVICE |
| A6 | LLM 模式供应商(国内可达)与其内容安全条款核查 | 选型后归档 | G1_LIVE 同源阻塞 |
| A7 | 输入护栏的正则缺口:真实儿童语音的误报/漏报率无法离线断定,试点前 2 周由成人用真实转写样本回放校准 | 试点前校准会 + 记录 | 同 A5 |
| A8 | CORS 收紧:局域网 MVP 默认 `*`,试点必须改为前台前端实际来源 | 部署清单项 | 同 A5 |

## 底线(不可越过)

- 生产/试点环境禁止 `ENGINE_PROVIDER=mock` 或 `ASR_PROVIDER=mock`。
- 禁止提交任何 API Key、真实儿童语音、转写、姓名、住址、学校等敏感数据到仓库。
- 未完成 A2(合规审核)前,不得让任何未成年人接触本系统。
