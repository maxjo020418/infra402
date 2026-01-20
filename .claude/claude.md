# AI Agent Deployment Instructions

## 🎯 Mission

infra402 모노레포를 Mini PC (Proxmox) + Tailscale + Vercel로 배포합니다.

---

## 📖 Documentation References

| File | Purpose |
|------|---------|
| [specs.md](file:///.claude/specs.md) | 아키텍처 사양 |
| [plan.md](file:///.claude/plan.md) | 배포 계획 |
| [task.md](file:///.claude/task.md) | 진행 상황 |

---

## 🔧 Quick Commands

### LXC 내부 (backend-services)
```bash
# Backend 실행
cd /opt/infra402/backend-proxmox && uv run python main.py  # :4021
cd /opt/infra402/backend-llm && uv run python pydantic-server.py  # :8000
```

### Tailscale
```bash
tailscale up                # 인증
tailscale funnel 8000       # 공개 엔드포인트
tailscale status            # 상태 확인
```

### Frontend
```bash
cd frontend
pnpm dev  # 로컬 개발
```

---

## ⚙️ Environment Setup

### Backend-LLM `.env`
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxx
PRIVATE_KEY=0x...
BACKEND_BASE_URL=http://localhost:4021
```

### Vercel Environment
```
VITE_CHAT_API_BASE=https://backend-services.tailnet-xxxx.ts.net
```

---

## ⚠️ Important Notes

1. **LXC nesting**: Tailscale 작동을 위해 `--features nesting=1` 필수
2. **Ports**: backend-llm:8000, backend-proxmox:4021
3. **Secrets**: `.env` 파일은 Git에 커밋 금지

---

## 🚀 Base App Migration

[Migration Guide](https://github.com/Basten1209/base_app_migration/blob/main/BASE_APP_MIGRATION_GUIDE.md)

### Quick Steps
1. **SDK 설치**: `pnpm add @farcaster/miniapp-sdk`
2. **App Ready**: `App.tsx`에 `sdk.actions.ready()` 추가
3. **Manifest 생성**: `public/.well-known/farcaster.json`
4. **Account Association**: [Base Build Tool](https://www.base.dev/preview?tab=account)에서 서명
5. **Embed Metadata**: `index.html`에 `fc:miniapp` 메타 태그 추가

### Account Association (Ownership 주의)
- **전용 지갑 사용 권장**: 개인 지갑 대신 앱 전용 지갑으로 서명
- Base Build Tool에서 URL 입력 → 지갑 서명 → `header`, `payload`, `signature` 복사
- `farcaster.json`에 값 입력

### Manifest Example
```json
{
  "accountAssociation": { "header": "", "payload": "", "signature": "" },
  "miniapp": {
    "version": "1",
    "name": "Infra402",
    "homeUrl": "https://your-domain.vercel.app",
    "iconUrl": "https://your-domain.vercel.app/icon.png"
  }
}
```
