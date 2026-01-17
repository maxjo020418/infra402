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
