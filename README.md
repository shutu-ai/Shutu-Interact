# AI English Greeter (Coco English) — MVP

前台 kiosk 应用:在深圳少儿英语培训中心前台,卡通机器人 Coco 通过语音与到访儿童(4–12 岁)进行 1–3 分钟的受控英语互动。方案见 `01_项目方案_AI_English_Greeter_MVP.md`,任务拆解见 `02_Codex任务提示词_AI_English_Greeter.md`,人工验收清单见 [docs/acceptance-checklist.md](docs/acceptance-checklist.md)。

## 技术栈

- **前端**:Vue 3 + Vite + TypeScript + Pinia + Vue Router + zod(边界校验)
- **后端**:Python + FastAPI + httpx(无数据库,内存会话)
- **语音**:浏览器 MediaRecorder 录音 → 后端 ASR → 对话引擎 → 浏览器 speechSynthesis 播报

## 目录结构

```
backend/
  app/
    api/routes/          # health / sessions / speech(语音回路+guard)/ guarding(防护接线)
    core/                # config(环境变量)、container(provider 装配,替换点)
    models/dialogue.py   # 领域常量与不可变模型(Turn/Session)
    providers/           # DialogueEngine/ASR/TTS/ChatClient 协议与实现
    schemas/             # 请求校验 + 统一响应 envelope
    services/            # SessionManager(TTL 清理)、SafetyGuard(内容防护)
    main.py              # FastAPI 入口(CORS、统一错误 envelope)
  tests/                 # 69 个后端测试
frontend/
  src/
    components/          # CocoCharacter / PrimaryButton / FullscreenToggle
    services/            # api(zod 校验客户端)、character、voice(录音/TTS)
    stores/session.ts    # 流程状态机 welcome→age→topic→session→end
    views/               # 5 个页面
    router/ types/       # 路由守卫、共享类型
  public/assets/         # Coco 角色素材(5 个状态)
docs/acceptance-checklist.md
```

## 启动方式(本地开发)

### 后端(默认 mock 引擎,无需任何 API key)

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt     # Windows;.venv/bin/pip on macOS/Linux
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev        # 默认调 http://127.0.0.1:8000,可用 VITE_API_BASE 覆盖(见 frontend/.env.example)
```

打开 http://localhost:5173,按 开始 → 年龄 → 主题 → 对话 走完整流程。

### 测试与构建

```bash
cd backend  && .venv/Scripts/python.exe -m pytest tests/ -q   # 69 passed
cd frontend && npm run test                                    # vitest,36 passed
cd frontend && npm run build                                   # vue-tsc 类型检查 + vite 构建
```

## 每阶段任务清单(方案 §8)

| Phase | 交付物 | 状态 |
|-------|--------|------|
| 1 可运行骨架 | 5 页面流程、角色素材接入、Mock 对话、统一 envelope | ✅ Tasks 1–2 |
| 2 真实语音 | 录音上传、ASR 接口、TTS 播报、对话回路、ASR 失败重试 1 次 | ✅ Task 3 |
| 3 受控对话与安全层 | LLM DialogueEngine + Prompt 模板 + 脚本回退、SafetyGuard(输入/输出)、会话 TTL 清理、匿名日志、统一错误处理 | ✅ Tasks 4–5 |
| 4 现场优化 | 大按钮 UI、全屏切换、返回导航、思考态/轮次进度、错误提示、CORS、部署文档 | ✅ Tasks 6–7 |

## Provider 替换点(方案 §9.7)

所有 provider 走 `typing.Protocol`,装配集中在 `backend/app/core/container.py`,路由只依赖协议。

| 能力 | 当前实现 | 替换方式 |
|------|----------|----------|
| 对话引擎 | `MockDialogueEngine`(脚本) | 设 `ENGINE_PROVIDER=llm` + `LLM_API_KEY` 等(OpenAI 兼容接口);任何 LLM 失败自动回退脚本引擎(§8.3) |
| 语音识别 ASR | `ASR_PROVIDER=mock`:`MockSpeechRecognizer`(固定返回)。**真实 ASR 已实现但尚未用真实凭据验证**:`ASR_PROVIDER=openai` 走 OpenAI 兼容 `POST {ASR_API_BASE}/audio/transcriptions`(`backend/app/providers/asr.py` 的 `OpenAICompatibleTranscriber`,离线合同测试覆盖) | 设 `ASR_PROVIDER=openai` + `ASR_API_KEY`/`ASR_API_BASE`/`ASR_MODEL`(不带 key 拒绝启动,绝不静默回退 mock);单文件冒烟:`backend/scripts/asr_smoke.py`(凭据只经环境变量)。路由 `/api/sessions/{id}/speech` 不变 |
| 语音合成 TTS | 浏览器 `speechSynthesis`(en-US, rate 0.9)——**过渡方案**:kiosk Chrome/Edge 内置,无需凭据,音质/音色不可控 | 云 TTS:后端 `POST /api/tts` 已是替换点(mock 返回静音 WAV),实现 `SpeechSynthesizer` 并改前端 `frontend/src/services/voice.ts` 的 REPLACEMENT POINT 注释处 |
| 提示词 | `app/providers/prompts.py` | 年龄分层、主题锁定、安全规则、漂移恢复均在此文件调整 |

## 延迟优化建议(方案 §8 Phase 4)

- 现状:半双工单次往返 `POST /speech`(上传→ASR→引擎→返回),浏览器 TTS 本地即时播放,已按 ≤3s 预算设计。
- 接真实 provider 后的顺序:① ASR/TTS 选就近区域节点;② TTS 流式(首句先播,后端分句返回);③ LLM 用低延迟模型 + `max_tokens` 限幅(已设 80);④ 引擎超时 6s 已配,超时走脚本回退保证流程不中断;⑤ 前台网络建议专线/热点,避免高峰拥塞。

## 部署说明(kiosk)

1. **后端**:`pip install -r requirements.txt` 后 `uvicorn app.main:app --host 0.0.0.0 --port 8000`(建议 systemd / NSSM 常驻)。
2. **前端**:`npm run build` 产出 `frontend/dist/`,用 nginx 或任意静态服务器托管;构建前设 `VITE_API_BASE` 指向后端地址。
3. **跨域**:默认 `CORS_ALLOW_ORIGINS=*`(局域网 MVP);生产收紧为前端实际来源,如 `CORS_ALLOW_ORIGINS=https://kiosk.example.com`。
4. **麦克风权限**:浏览器 `getUserMedia` 只在安全上下文可用——平板 kiosk 必须走 `https://`(或用 `localhost` 调试);建议配内网证书 + 域名。
5. **全屏**:页面右上角 `⛶ 全屏` 按钮进入全屏;浏览器开自启 + 指定首页即可作为 kiosk 常驻。
6. **LLM 模式**:`.env` 设 `ENGINE_PROVIDER=llm` 与 `LLM_API_KEY`(见 `backend/.env.example`);不带 key 启动 llm 模式会直接报错退出(mock 模式无此要求)。
7. **真实 ASR 模式**:同上设 `ASR_PROVIDER=openai` 与 `ASR_API_KEY` 等方可启动;验收前用 `backend/scripts/asr_smoke.py` 以成人英文音频(如 "I like cats.")做单文件冒烟。生产/试点禁止 `ENGINE_PROVIDER=mock` 或 `ASR_PROVIDER=mock`。

## 合规注意(方案 §7)

- 不采集姓名/电话/住址/学校等 PII;SafetyGuard 双向拦截 PII 问题、暴力/成人/医疗/法律/金钱内容、秘密依赖话术,命中即换脚本安全回复。
- 日志只记会话 ID + 匿名原因类别,不落任何童声文本或转写内容;会话 TTL(默认 600s)到期自动清理,`end` 即删。
- 儿童文本仅保存在内存会话中,服务重启即清空。
