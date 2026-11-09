# Shutu-Interact — Coco English 两分钟真实语音 MVP 闭环任务

> **执行对象**：Codex CLI / Codex Windows（在仓库根目录执行）  
> **仓库**：https://github.com/shutu-ai/Shutu-Interact  
> **任务版本**：2026-11-09 / MVP Closure v1  
> **评审基线**：`master`，`fc46da5b69b9405a72aff82529965bce525da186`  
> **目标用户**：深圳少儿英语培训中心前台、4–12 岁儿童、单次 1–3 分钟（目标约 2 分钟）  
> **状态定义**：此文档是**待执行任务**，不是验收通过证明。涉及未成年人的真实试点必须先完成机构合规审核与监护人授权。

## 0. 给 Codex 的执行指令（完整阅读并执行）

你是本仓库的资深全栈工程师、儿童语音产品工程师及独立质量验收责任人。你的任务不是继续堆功能，而是**把一个小朋友在前台与 Coco 自然、安全、可控地用英语交流两分钟**真正实现并用证据验证。

**执行纪律：**

1. **先检查现状，后修改**：读取实际仓库、Git 状态、最近提交、配置和测试文件；本文所列故障均基于上述评审 SHA，若分支已更新，以新代码为准逐条复核，不要机械重复已修复的问题。
2. **事实与证据分开**：每个任务标注 `未开始/进行中/完成/阻塞`；“代码存在”“Mock 测试通过”“真实服务集成成功”“真实设备验收通过”是四种不同的结论，不能混为一谈。
3. **优先级**：P0（可运行与真实语音）→ P1（安全、隐私、交互稳定）→ P2（CI、可部署和验收）；涉及儿童个人数据的防护和试点门禁不得降级。
4. **禁止假通过**：不能用固定返回 `I like dogs.` 的 Mock ASR 宣称儿童语音识别成功；不能用静音 WAV 宣称 TTS 成功；没有凭据/设备时用 `BLOCKED_*` 说明，并完整完成可离线验证的部分。
5. **资源与架构节制**：保留 Vue 3 + Vite + TypeScript + Pinia / FastAPI 的当前结构；保留 `SpeechRecognizer` / `DialogueEngine` / `SpeechSynthesizer` 接口。不引入多 Agent、复杂数据库、儿童账号、摄像头、声纹、3D 数字人、长期记忆。
6. **接口兼容**：尽量维持已用的 `/api/sessions`、`/api/sessions/{id}/replies`、`/api/sessions/{id}/speech`、`/api/sessions/{id}/end`；需要调整响应字段时做受控迁移、同步更新前后端与测试，并在文档中列清兼容性影响。
7. **敏感信息保护**：禁止提交 API Key、真实儿童语音、转写、姓名、地址、学校等敏感数据；不要把原始转写、上传音频、异常中携带的模型响应打印进日志。
8. **运行和安全边界**：仅对本仓库及其自建测试环境进行操作；不要直接部署到真实前台或接触儿童。任何真实儿童现场试点都需要明确的人工作业和合规许可门禁。
9. **交付要求**：每个阶段提供最小变更、测试证据、失败原因、可复现命令；完成前必须提交一份机器可读验收结果和简短的人工验收清单。
10. **代码审查**：发现本文遗漏的启动错误、隐私风险或状态机缺陷，要主动补充最小修复，不要绕过测试；每阶段收尾 `git diff --check`，保持变更可审查。

---

## 1. 当前仓库的已核实基线

### 1.1 已具备（代码层面）

- 前端五个页面（欢迎、年龄、主题、互动、结束）与 Coco 透明素材（idle / greeting / listening / thumbsup）。
- 后端 FastAPI 路由、会话管理、Mock 脚本对话、LLM 对话引擎、年龄/主题 Prompt、安全规则和部分匿名日志。
- 前端 `MediaRecorder` 录音，浏览器 `speechSynthesis` 播报，文本兜底输入。
- Python pytest 与前端 Vitest 测试代码；README **声称**后端 63 个、前端 34 个测试通过，但在评审时未发现 GitHub Actions 运行记录，需重新实际执行。

### 1.2 已核实的问题（必须重新复核）

| 编号 | 严重度 | 文件/位置 | 评审发现 | 期望 |
|---|---|---|---|---|
| B-01 | P0 | `backend/app/providers/mock_dialogue.py` | 使用 `Tuple` 类型但仅 `from typing import Mapping` | 导入不报 `NameError`，应用可启动 |
| B-02 | P0 | `backend/app/providers/asr.py`、`backend/app/core/container.py` | `MockSpeechRecognizer` 固定输出 `I like dogs.`，真实 ASR 没接通 | 合规测试音频得到真实且不同的转写 |
| B-03 | P0 | `backend/app/providers/tts.py` | 后端 Mock TTS 生成静音 WAV | 云 TTS 若标记可用必须能播放真实声音；浏览器 TTS 可作为明确的临时方案 |
| B-04 | P0 | 欢迎页/语音链路 | 当前说“不收集任何个人信息”，但会上传音频并在内存保存转写 | 告知内容真实准确、明确授权与访问边界 |
| B-05 | P1 | `frontend/src/stores/session.ts` | ASR 失败只重传同一录音 | 引导孩子重新录一段，最多一次重录 |
| B-06 | P1 | `frontend/src/services/voice.ts`、Store | TTS 与麦克风缺乏互斥控制 | Coco 播放时禁止录音；退出/切页能停止播放和录音 |
| B-07 | P1 | `frontend/src/views/EndView.vue`、Store | 自然结束后点击“返回首页”才请求结束服务端会话 | 到达终局自动删除或立即撤销后台会话；成功/失败均本地清理 |
| B-08 | P1 | `backend/app/api/routes/speech.py` | `await audio.read()` 未见大小/时长上限，接口返回原始转写 | 请求限额、校验、日志与响应最小化 |
| B-09 | P1 | `backend/app/services/safety_guard.py` | 主要按简单关键词过滤，未全面处理儿童自报个人信息 | 加强隐私拦截与可测试的安全策略，不能依赖正则做唯一防线 |
| B-10 | P2 | `backend/app/providers/prompts.py`、`README.md`、`CocoCharacter.vue` | Prompt/README 称 Coco 为 camel，而 PNG 为蓝橙机器人 | 文案与图片设定统一为 Friendly Robot |
| B-11 | P2 | GitHub Actions | 评审时 `/actions/runs` 为空 | 建立 CI，提供可追溯测试结果 |
| B-12 | P1 | 浏览器设备与云服务配置 | 尚无真实设备、弱网、儿童口音效果证据 | 真实设备/云服务联调验收，不以 Mock 替代 |

**额外关注（审计中验证，不作未经验证的断言）：**
- API 请求中同步网络 I/O 是否阻塞事件循环；LLM 6 秒超时和用户期望延迟是否匹配。
- 结束页面是否可能被路由状态重置干扰；多次点击开始/停止/退出是否竞态。
- 原始音频 MIME 类型、设备编码（`webm`/`mp4` 等）与所选 ASR API 的实际兼容情况。
- 未经过安全过滤或脱敏的 `transcript` 是否出现在接口响应、前端状态和日志中。
- Session ID 与访问边界是否足够防止共享设备之间的会话访问，是否需要短 TTL、一次性授权和限流。

---

## 2. 目标用户流程与体验约束

**人机交互契约：**

```text
欢迎（明确显示 AI）
  → 成人确认告知/授权后点击开始
  → 选择年龄段：4–6 / 7–9 / 10–12
  → 选一个主题：animals / colors / fruits / sports / hobbies
  → Coco 播放一句简短英语欢迎语并提问
  → Coco 停止播放、开始等待孩子按键说话
  → 孩子录音 → ASR → 输入安全/隐私检查 → 受控 LLM/脚本
  → 输出安全检查 → Coco 英语播报（同时显示文本）
  → 重复 3–5 轮，目标约两分钟
  → 结束鼓励 → 立即结束服务端会话与清理客户端临时状态
  → 可立即关闭或回到欢迎页，等待下一位孩子
```

- 核心用户是 4–12 岁儿童，年龄只是难度初始选择，不作为真实语言能力评估。
- AI 一次只问一个问题，优先简短英语（4–6 岁可用单词回答）；孩子不理解可提示一句简短中文，但不转为长篇中文聊天。
- 允许随时退出，安静或不愿答时不能施压；允许一次重新录音，仍失败则触摸式答案或友好结束。
- **Mock 模式仅供开发与成人测试**；真实儿童试点必须采用已验证的语音链路并完成授权、合规和现场门禁。

---

## 3. 分阶段开发任务与验收门禁

### G0 — 代码基线修复和可重复测试（P0）

**工作项：**

- [ ] 检查 `master` HEAD 和 Git 状态，在报告中记录实际 SHA；新建独立工作分支（名称自定），保留用户未提交的修改。
- [ ] 修复 B-01：`Tuple` 导入错误；运行最小导入测试及 FastAPI 健康检查。
- [ ] 修复其他能阻止 `uvicorn` 启动、`pytest`、`npm test`、`npm run build` 的错误（仅做必要变更）。
- [ ] 验证后端路由契约/状态码、前端构建与文字 Mock 全链路。
- [ ] 统一 README 中的实测数字与命令：不能复制旧的 `63 passed / 34 passed` 作为本次证据。

**验收命令（根据实际平台调整路径）：**

```powershell
# Windows PowerShell 示例；从仓库根目录进入
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -c "from app.main import app; print(app.title)"

cd ..\frontend
npm ci
npm run test
npm run build

cd ..
git diff --check
```

**通过标准：**后端可导入/启动，自动化测试与前端构建全部通过，报告有实际命令、日期和 PASS 数；否则 `G0=FAIL`，不得宣称完成后续阶段。

### G1 — 真实英语语音识别与可用播报（P0）

**工作项：**

- [ ] 在现有 `SpeechRecognizer` 协议下实现**一个真实**英语 ASR Provider。优先选择中国境内可用、提供合规处理条款的服务商，先确认音频格式、定价、商用政策、日志/训练留存策略与数据地域。
- [ ] 通过 `ASR_PROVIDER=mock|<provider>` 显式选择；无有效凭据时不能悄悄落到 mock 并被误报为真实识别成功。生产/试点环境禁止启用 mock。
- [ ] 支持浏览器实际上传的 MIME/编码；服务端根据供应商要求进行最小必要转码（如需要），验证格式不匹配时给可理解错误。
- [ ] 使用**成人本人或已授权合成**的英语测试音频，至少分别输入 `I like cats.` / `I like dogs.` / `My favorite color is blue.`，确认转写正确反映不同声音输入。不得使用真实儿童录音作为默认测试资产。
- [ ] TTS 可暂用浏览器 `speechSynthesis`，但需在目标设备测英文发音、播报音量、语言包、可用声音。若切换云端 TTS，则实现真正可听的音频、播放失败处理，不能用静音 WAV 标记完成。
- [ ] 增加 Provider 合约测试（HTTP Mock/录音格式/超时/配额/空转写/无密钥），并编写一个使用真实凭据时才运行的手动烟测脚本（不要提交密钥）。

**验收门槛：**

- `G1_OFFLINE=PASS`：所有 Provider 测试可在无密钥环境运行且通过；Mock 明确显示为 Mock。
- `G1_LIVE=PASS`：实际 API 处理不同英语录音，返回不同且正确的内容，Coco 可完成一轮真实语音往返，证据包含供应商、配置项、延迟和匿名化结果（不保留儿童音频/原文）。
- 缺凭据时必须记录 `G1_LIVE=BLOCKED_CREDENTIALS`，不得写 PASS。

### G2 — 两分钟对话状态机和共享设备安全（P1）

**工作项：**

- [ ] 明确定义状态 `idle / speaking / listening / processing / finished / error`，与 PNG 角色的映射集中维护（现有 `greeting/listening/praise` 服务端状态可以兼容）。
- [ ] **严格半双工**：播放 Coco 声音时禁用开始录音；点击退出/浏览器离开/重置时立即停止 `speechSynthesis`、录音器和媒体轨道；异步过期响应不能更新新会话。
- [ ] ASR 第一次失败后提示“没听清，请再说一次”，**录制一段新的音频**，最多允许一次重录；第二次仍失败提供触控按钮或友好结束，不重复发送原音频。
- [ ] 结束逻辑改为自然结束后自动清除服务端会话（无需等待用户点击“返回首页”）；保留最后一句结束语直到播放完成或超时，再返回欢迎页；清理不会导致最后一句消失或中断。
- [ ] 设置互动时长上限（例如 180 秒，可配置），空闲超时、网络错误、浏览器切后台和麦克风拒绝时安全退出；后端短 TTL 作为兜底。
- [ ] 处理并发点击、请求取消、长响应、过期 session 404、网络中断、页面刷新与浏览器返回；不得保留上一位孩子的文字或播放上一位孩子的声音。
- [ ] 不在客户端 localStorage、sessionStorage 或持久缓存写入儿童对话文本；默认仅内存使用。

**验收门槛：**

- 任一状态能退出；对话自然结束后服务端 Session 不可再查询/回复（404 或等价终止语义）。
- 人工测试：连续两人模拟使用，第二位看不到第一位的任何对话文字，也不会听到前一位未播完的音频。
- 录音时绝不播放 AI 语音；AI 播放时绝不录音；ASR 失败使用新录音重新尝试。
- 3–5 轮、1–3 分钟的受控对话路径可重复执行。

### G3 — 儿童隐私、内容安全与 API 防护（P0/P1）

> 注意：技术措施只为法律合规提供支持，**不能代替深圳办学/学科培训资质核实、儿童监护人授权、云厂商数据处理协议评审**。

**工作项：**

- [ ] 清理虚假/过度绝对的隐私文案，特别是欢迎页的“不收集任何个人信息”。如会上传声音、暂存转写，应明确告知这些事实、用途、处理方、保存策略、联系/退出方式。
- [ ] 设计 **成人/监护人确认入口**；没有授权不开放麦克风。授权流程的真实有效性由机构合规负责人确认；不能用简单的“老师代点开始”代替所有场景下所需的监护人同意。
- [ ] 前台默认不要求儿童输入姓名/电话/住址/学校；不设儿童账号、不保存原始录音、不建声纹；云端服务不得把儿童数据用于模型训练，除非满足适用法律及明确授权（本 MVP 不设计该用途）。
- [ ] 审核输入/输出链路：对自报电话、姓名、地址、学校、家庭信息等尽可能在上传 LLM 前脱敏/阻断；输入安全层、模型提示词、输出安全层三重约束；保留最小化会话状态。
- [ ] 对服务端返回 `transcript` 的必要性进行评审：默认不返回完整儿童转写；必要调试仅限开发测试并脱敏，不在前台展示敏感内容。
- [ ] 对安全规则增加测试集：隐私问询、危险话题、模型越权、劝孩子保密/离开监护人、通过中文/拼写变体绕过、提示词注入、正常有用的安全回答；减少误杀，避免把寻求帮助的儿童一律沉默处理。
- [ ] 服务端限制音频**大小、格式、合理时长**，避免无上限 `await audio.read()`；加入频率限制/超时、异常输入处理；所有模型凭据只放服务端。
- [ ] 审核会话 ID、日志、异常堆栈、第三方 SDK、监控与代理是否可能暴露音频和转写；禁止日志和遥测泄漏儿童内容。
- [ ] 编写 `docs/privacy-and-pilot-gates.md`：机构资质与学科培训边界、监护人同意、数据存储/传输地域、厂商条款、内容标识、删除流程、现场负责人和暂停机制，逐项用 `已核查/待核查` 记录。**不得自行宣称法律合规已完成**。
- [ ] 修改 Coco 身份文案为“AI 英语互动机器人 Coco”，与蓝橙色机器人 PNG 一致；避免长期陪伴、排他依赖等文案。

**验收门槛：**

- `G3_TECH=PASS`：安全与隐私自动测试通过；不存在默认保存录音、无上限上传、密钥下发到前端等已知高风险问题。
- `G3_LEGAL=BLOCKED_REVIEW`：若未经机构/法务/监护人流程确认，必须保留阻塞状态；**不能进入儿童真实试点**。

### G4 — CI、文档、部署和可追溯质量（P2）

**工作项：**

- [ ] 添加 `.github/workflows/ci.yml`：推送及 PR 时运行后端 pytest、前端 Vitest、`npm run build`，如条件允许再加 Python 编译/类型或 lint 检查。
- [ ] CI 全部使用 Mock 和虚拟测试素材；**禁止在公开仓库 CI 上传真实儿童声音或泄漏 API Key**。真实服务烟测单独手动触发、遵守安全权限。
- [ ] 补齐 `backend/.env.example`：ASR provider、必要区域/模型、timeout、上传大小与时长限制、会话时长等；所有 `.env.example` 中不得出现真实密钥。
- [ ] 统一 `README.md`：开发 Mock 模式、真实语音模式、启动方式、前台 HTTPS/麦克风权限、浏览器兼容、生产禁止 Mock、验收状态、已知限制和供应商的数据处理边界。
- [ ] `docs/acceptance-checklist.md` 划分“自动测试已通过”“真实 ASR 已验证”“真实设备验收”“儿童试点合规门禁”四个类别；人工项默认未勾选。
- [ ] 提供一个可复现的故障演练矩阵：网络断开、ASR 空结果、TTS 不可用、API 超时、过期会话、重复点击、多用户轮换、语言包缺失。
- [ ] 提交证据文件 `docs/evidence/mvp-closure-report.md`、`docs/evidence/mvp-closure.json`，JSON 包含 git SHA、测试命令、结果、真实 API 验证状态、设备状态、法律审查状态与阻塞项。

**验收门槛：**在同一提交 SHA 上 CI 显示真实 PASS；README 的测试数字与运行记录一致。没有 CI 结果时不能说 `G4=PASS`。

### G5 — 真实设备与现场门禁（不得以自动化替代）

**成人/授权模拟测试清单：**

- [ ] 前台目标浏览器/平板使用 HTTPS，麦克风权限可控，能正常采集英语语音。
- [ ] 成人使用三种英语难度、不同语速与短句完成对话，不因 ASR 错误陷入死循环。
- [ ] 在有背景交谈的室内环境测试，记录识别失败率和主观可听度。
- [ ] 测量“停止录音 → Coco 开始播报”的 P50 / P90（至少 30 次成人测试样本），记录测试设备、网络、Provider 和方法；**P90 ≤3 秒为目标值，不能未经测量宣称达标**。
- [ ] 连续运行 30 次模拟会话，记录退出、切页、录音轨道和 Session 清理是否正确。
- [ ] 不保存儿童原音频或可识别转写，不将真实儿童数据用于测试素材。
- [ ] 试点前完成机构办学/课程边界核查、监护人授权文本及实际授权机制、云端数据处理评审和现场工作人员培训。

**结果定义：**

- `G5_DEVICE=PASS`：有真实设备、实测数据、环境与缺陷清单。
- `G5_PILOT=PASS`：仅在获得可核实的机构及监护人合规确认后方可标记；否则必须 `BLOCKED_COMPLIANCE`。

---

## 4. 推荐执行顺序与提交要求

建议按五个小提交或五个 PR/阶段审查执行，不要求一次性交付庞大重构：

1. `fix: restore backend import and green local test baseline` —— G0
2. `feat: pluggable real ASR provider and honest voice status` —— G1
3. `fix: half-duplex session lifecycle and recovery` —— G2
4. `security: child privacy gates and bounded speech upload` —— G3
5. `ci: reproducible checks and mvp acceptance evidence` —— G4

完成当前阶段并验证后，再进入下一阶段。无 API 凭据时，允许继续实现 G2/G3/G4 的可离线部分，不能假称 G1_LIVE 完成；无真实平板时保留 G5_DEVICE 阻塞。

**变更文件预计包括但不限于：**

```text
backend/app/providers/mock_dialogue.py
backend/app/providers/asr.py
backend/app/providers/tts.py
backend/app/core/config.py
backend/app/core/container.py
backend/app/api/routes/speech.py
backend/app/api/routes/guarding.py
backend/app/services/safety_guard.py
backend/app/services/session_manager.py
backend/tests/*
frontend/src/services/voice.ts
frontend/src/stores/session.ts
frontend/src/views/WelcomeView.vue
frontend/src/views/SessionView.vue
frontend/src/views/EndView.vue
frontend/src/components/CocoCharacter.vue
frontend/src/**/*.spec.ts
.github/workflows/ci.yml
README.md
docs/acceptance-checklist.md
docs/privacy-and-pilot-gates.md
docs/evidence/mvp-closure-report.md
docs/evidence/mvp-closure.json
```

不要为满足文件清单而制造无关改动；按实际问题实施。

---

## 5. 最终验收指标（不能混用）

| 领域 | 建议目标 | 验收方法 |
|---|---|---|
| 运行 | 后端启动成功、前端构建成功 | 本地命令 + CI |
| 功能 | 3 年龄段、5 主题、3–5 轮 | 自动测试和人工走通 |
| 真实识别 | 不同英语录音得到不同准确文本 | 真实 ASR + 成人/合成授权音频 |
| 真实发声 | Coco 语音清晰、设备可播 | 真实目标设备听测 |
| 延迟 | 停止录音至语音开始 P90 ≤3 s，目标而非事实 | ≥30 次实测 |
| 安全 | 已知高风险测试集 0 违规输出 | 测试集 + 人工抽查；不等于对一切未知输入的零风险保证 |
| 隐私 | 个人信息最小化、无需儿童账户、无原音频持久化 | 源码审计 + 厂商与部署核查 |
| 清理 | 退出/自然结束/异常后不串话 | 集成测试 + 连续多用户模拟 |
| 稳定 | 连续 30 次模拟会话无阻断级故障 | 实机记录 |
| 合规 | 有机构审核和监护人授权证据 | 机构/专业人士负责确认 |

### 机器可读结果结构（示例，初始值不得填 PASS）

```json
{
  "repository": "shutu-ai/Shutu-Interact",
  "base_sha": "fc46da5b69b9405a72aff82529965bce525da186",
  "evaluated_sha": null,
  "G0": "NOT_RUN",
  "G1_OFFLINE": "NOT_RUN",
  "G1_LIVE": "BLOCKED_CREDENTIALS",
  "G2": "NOT_RUN",
  "G3_TECH": "NOT_RUN",
  "G3_LEGAL": "BLOCKED_REVIEW",
  "G4": "NOT_RUN",
  "G5_DEVICE": "BLOCKED_DEVICE",
  "G5_PILOT": "BLOCKED_COMPLIANCE",
  "tests": {"backend": null, "frontend": null, "build": null},
  "latency_p90_ms": null,
  "blocking_issues": [],
  "evidence_paths": []
}
```

## 6. Codex 最终回复必须包含

1. 本次开始/结束 SHA、分支、提交情况、改动摘要。
2. G0–G5 各门禁状态；区分 `PASS / FAIL / BLOCKED_* / NOT_RUN`。
3. 实测命令与真实输出统计，不引用历史 README 里的未经复核 PASS。
4. 已解决的 B-01～B-12 问题表及尚存风险。
5. 明确写出：**当前可否用于成人 Demo、可否用于真实儿童现场试点**，不可只说“项目完成”。
6. 如果被外部凭据、设备或机构审批阻塞：给出精确下一步和所需输入，但不要宣称工作已经完成。

---

## 7. 执行入口

进入仓库目录后，可以把本文件内容交给 Codex：

```powershell
cd D:\dev-projects\Shutu-Interact
# 请 Codex 读取：Shutu-Interact_Codex_MVP_Closure_Task_2026-11-09.md
```

**任务完成定义（DoD）：**

> 一个获得许可的测试者在前台目标设备上，实际说出不同英语句子，Coco 能正确理解并自然回答，完成约两分钟的适龄、受控、可安全退出互动；会话随后自动清理，测试与合规状态有可复核的证据。

**DoD 未满足时，请报告具体阻塞与剩余任务，而不是宣布全面完成。**
