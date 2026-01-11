# AI Agent Deployment Instructions

## 🎯 Mission

infra402 모노레포의 하이브리드 배포 가이드를 수행합니다:
- **Frontend**: Vercel에 배포
- **Backend**: Local MacBook에서 실행
- **Tunnel**: Cloudflare Tunnel로 외부 연결

---

## 📖 Documentation References

작업 전 반드시 아래 문서를 참조하세요:

| File | Purpose |
|------|---------|
| [specs.md](file:///.claude/specs.md) | 아키텍처 사양 및 컴포넌트 정의 |
| [plan.md](file:///.claude/plan.md) | 단계별 구현 계획 |
| [task.md](file:///.claude/task.md) | 현재 진행 상황 트래킹 |

---

## 🔧 Quick Commands

### Frontend (Vercel)
```bash
cd frontend
pnpm install
pnpm dev          # Local development (http://localhost:5173)
pnpm build        # Production build
```

### Backend LLM
```bash
cd backend-llm
uv sync
uv run python pydantic-server.py   # Runs on :8000
```

### Backend Proxmox
```bash
cd backend-proxmox
uv sync
uv run python main.py             # Runs on :4021
```

### Cloudflare Tunnel
```bash
# 터널 생성 (최초 1회)
cloudflared tunnel create infra402-api

# 터널 실행
cloudflared tunnel run --url http://localhost:8000 infra402-api
```

---

## ⚙️ Environment Setup

### Frontend `.env`
```env
VITE_CHAT_API_BASE=https://api.mydomain.com
```

### Backend-LLM `.env`
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxx
PRIVATE_KEY=0x...
BACKEND_BASE_URL=http://localhost:4021
```

---

## 🔄 Workflow

1. **Read** `task.md` → 현재 단계 확인
2. **Check** `plan.md` → 해당 단계 상세 지침 확인
3. **Execute** → 작업 수행
4. **Update** `task.md` → 완료 표시
5. **Continue** → 다음 단계로 진행

---

## ⚠️ Important Notes

1. **Sleep Mode**: MacBook의 Sleep Mode 방지는 사용자가 수동으로 설정
2. **CORS**: Backend에서 Vercel 도메인 허용 필요
3. **Secrets**: `.env` 파일은 절대 Git에 커밋하지 않음
4. **Ports**: 
   - Frontend Dev: 5173
   - Backend LLM: 8000
   - Backend Proxmox: 4021
