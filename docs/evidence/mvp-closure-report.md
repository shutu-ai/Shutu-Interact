# MVP Closure 证据报告 — 2026-11-09

分支 `feature/mvp-closure`,base `fc46da5b`,evaluate 于 `c6f46a0`(此后仅追加 docs/CI/evidence 文件,未改应用代码)。机器可读版:[mvp-closure.json](mvp-closure.json)。

## 门禁状态

| 门禁 | 状态 | 依据 |
|------|------|------|
| G0 基线 | **PASS** | B-01(`Tuple` 未定义注解,PEP 649 下被 3.14 掩码)改为内建 `tuple[...]`;新增 `test_app_imports.py` 强制求值全部注解;uvicorn 可启动;本地 122 通过,CI 3.12 严格注解证明修复 |
| G1 真实 ASR | **PASS(离线合同)** / G1_LIVE=**BLOCKED_CREDENTIALS** | `OpenAICompatibleTranscriber` 实现 SpeechRecognizer 协议;`ASR_PROVIDER=mock\|openai` 显式选择,openai 缺 key 拒绝启动(绝不静默回退);13 个离线合同测试;`scripts/asr_smoke.py` 就绪,但本环境无凭据,真实调用未发生 |
| G2 会话生命周期 | **PASS** | 严格半双工;flowEpoch 防旧响应串新会话;ASR 失败重录新音频(预算 1,绝不重发原音频);自然结束即删服务端会话;180s 总上限 + 60s 闲置;404 恢复;退出停止合成与录音轨 |
| G3 隐私与安全 | **PASS** | 诚实隐私文案(移除"不收集任何个人信息");家长/监护人确认门;输入侧 PII 自披露/注入护栏(中英,求助不静音);转写不回传;5MB/类型有界上传;会话级限流;凭据仅服务端;机器人身份;[privacy-and-pilot-gates.md](../privacy-and-pilot-gates.md) 已核查 13 项 |
| G4 CI 与证据 | **PASS** | ci.yml 已提交(pytest 3.12 + vitest + build,mock-only,无密钥);.env.examples 完备;README 以实测数字修订;四类验收清单 + 故障演练矩阵;CI 在推送 SHA `fd542a5` 上真实运行且全绿([run 42657133797](https://github.com/shutu-ai/Shutu-Interact/actions/runs/42657133797):backend (3.12) 12s,frontend 26s) |
| G5 设备 | **BLOCKED_DEVICE** | 本环境无目标平板/大屏/真实麦克风;延迟 p90 未测(json 中为 null,不填猜测值) |
| G5 试点 | **BLOCKED_COMPLIANCE** | 合规审核(A2)、监护人授权形式(A3)、供应商留存政策(A1)、CORS 收紧(A8)未关闭;关闭前禁止真实儿童接触 |

## 实测命令与结果

```
backend/.venv/Scripts/python.exe -m pytest tests/ -q
→ 122 passed (Python 3.14 local; CI also runs 3.12)

cd frontend && npx vitest run --reporter=basic
→ Test Files  12 passed (12) / Tests  48 passed (48)

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
| (本次) | G4 | 证据回填:CI run 42657133797 全绿 |

## DoD 判定

> 一个获得许可的测试者在前台目标设备上,实际说出不同英语句子,Coco 能正确理解并自然回答,完成约两分钟的适龄、受控、可安全退出互动;会话随后自动清理。

**未满足。** 缺口:真实 ASR 未用真凭据验证过(BLOCKED_CREDENTIALS)、无目标设备(BLOCKED_DEVICE)、无合规审批(BLOCKED_COMPLIANCE)。当前系统能做到的:成人用文字输入在本地完整走通流程(mock 引擎 + mock ASR,自动化测试覆盖全部边界)。**可否用于成人 Demo:可以(本地,明确标注 mock)。可否用于真实儿童现场试点:不可以**——需依次关闭 G1_LIVE、G5_DEVICE、G5_PILOT(见 blocking_issues)。

## 阻塞与解锁顺序

1. 取得 ASR 供应商凭据 → `scripts/asr_smoke.py` 冒烟(G1_LIVE)
2. 目标设备部署(HTTPS/麦克风权限)→ 按 acceptance-checklist §三 现场验收,回填 `latency_p90_ms`(G5_DEVICE)
3. 机构合规 + 监护人授权 + 供应商条款归档(G5_PILOT)
4. 试点前:确认两个 PROVIDER 均非 mock,CORS 收紧
