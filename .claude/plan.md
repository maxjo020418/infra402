# infra402 Deployment Plan

## Overview

하이브리드 아키텍처 배포를 위한 단계별 구현 계획입니다.

---

## Phase 1: Prerequisites 확인

### 1.1 로컬 환경 확인
- [ ] Node.js 18+ 설치 확인: `node -v`
- [ ] pnpm 설치 확인: `pnpm -v`
- [ ] Python 3.11+ 설치 확인: `python --version`
- [ ] uv 설치 확인: `uv --version`
- [ ] cloudflared 설치 확인: `cloudflared --version`

### 1.2 설치 명령어 (필요시)
```bash
# pnpm 설치
npm install -g pnpm

# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# cloudflared 설치 (macOS)
brew install cloudflared
```

### 1.3 계정 및 API Key 준비

| 항목 | 확인 | 비고 |
|------|------|------|
| Vercel 계정 | [ ] | [vercel.com](https://vercel.com) |
| Cloudflare 계정 | [ ] | [dash.cloudflare.com](https://dash.cloudflare.com) |
| 도메인 (Cloudflare 연결) | [ ] | `api.mydomain.com` 사용 예정 |
| OpenAI API Key | [ ] | [platform.openai.com](https://platform.openai.com) (택1) |
| Flock.io API Key | [ ] | [flock.io](https://flock.io) (택1) |
| EVM Wallet Private Key | [ ] | x402 결제 서명용 |
| Proxmox 접근권한 | [ ] | 이미 설정되어 있어야 함 |

> [!NOTE]
> LLM Provider는 OpenAI 또는 Flock.io 중 **하나만** 준비하면 됩니다.

---

## Phase 2: Backend 설정 및 실행

### 2.1 Backend-Proxmox 설정
```bash
cd backend-proxmox
cp .env-local .env
# .env 파일 편집하여 필요한 값 설정
uv sync
```

### 2.2 Backend-LLM 설정
```bash
cd backend-llm
cp .example.env .env
```

`.env` 파일 내용:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
PRIVATE_KEY=0xYourWalletPrivateKey
BACKEND_BASE_URL=http://localhost:4021
```

### 2.3 CORS 설정 확인

현재 `pydantic-server.py`에서 CORS는 `allow_origins=["*"]`로 설정되어 있음.
프로덕션에서는 아래로 변경 권장:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://infra402.vercel.app",
        "http://localhost:5173",  # 로컬 개발용
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2.4 Backend 실행 (터미널 2개 필요)

**Terminal 1 - Proxmox Backend:**
```bash
cd backend-proxmox
uv run python main.py
# → http://localhost:4021
```

**Terminal 2 - LLM Backend:**
```bash
cd backend-llm
uv run python pydantic-server.py
# → http://localhost:8000
```

---

## Phase 3: Cloudflare Tunnel 설정

### 3.1 Cloudflare 로그인
```bash
cloudflared tunnel login
# 브라우저에서 인증 완료
```

### 3.2 터널 생성
```bash
cloudflared tunnel create infra402-api
# → Tunnel ID 및 credentials 파일 생성됨
```

### 3.3 DNS 설정
```bash
cloudflared tunnel route dns infra402-api api.mydomain.com
# → Cloudflare DNS에 CNAME 레코드 자동 추가
```

### 3.4 설정 파일 생성

`~/.cloudflared/config.yml`:
```yaml
tunnel: infra402-api
credentials-file: /Users/hyeokx/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: api.mydomain.com
    service: http://localhost:8000
  - service: http_status:404
```

### 3.5 터널 실행
```bash
cloudflared tunnel run infra402-api
```

### 3.6 (선택) 시스템 서비스로 등록
```bash
sudo cloudflared service install
sudo launchctl start com.cloudflare.cloudflared
```

---

## Phase 4: Frontend 설정 및 Vercel 배포

### 4.1 환경변수 설정
```bash
cd frontend
echo "VITE_CHAT_API_BASE=https://api.mydomain.com" > .env
```

### 4.2 Frontend 코드 수정 (API URL 사용)

`src/` 내 API 호출 시 환경변수 사용 확인:
```typescript
const API_BASE = import.meta.env.VITE_CHAT_API_BASE || 'http://localhost:8000';
fetch(`${API_BASE}/chat`, { ... });
```

### 4.3 로컬 테스트
```bash
cd frontend
pnpm install
pnpm dev
# http://localhost:5173 에서 확인
```

### 4.4 Vercel 배포

**Option A - Vercel CLI:**
```bash
npm i -g vercel
cd frontend
vercel
# 프롬프트 따라 설정
```

**Option B - Vercel Dashboard:**
1. [vercel.com](https://vercel.com) 접속
2. New Project → Import Git Repository
3. Root Directory: `frontend` 설정
4. Environment Variables 추가:
   - `VITE_CHAT_API_BASE` = `https://api.mydomain.com`
5. Deploy 클릭

---

## Phase 5: 통합 테스트

### 5.1 Backend 헬스체크
```bash
curl https://api.mydomain.com/info
# → JSON 응답 확인
```

### 5.2 Frontend-Backend 연동 테스트
1. https://infra402.vercel.app 접속
2. Chat UI에서 메시지 전송
3. 응답 수신 확인

### 5.3 CORS 테스트
브라우저 개발자 도구 → Network → API 요청이 200 OK인지 확인

---

## Phase 6: 운영 안정화

### 6.1 MacBook Sleep 방지
**System Settings → Lock Screen:**
- "Turn display off on power adapter when inactive" → Never
- "Prevent automatic sleeping on power adapter when display is off" → Enable

**또는 caffeinate 사용:**
```bash
caffeinate -dimsu &
```

### 6.2 Backend 자동 시작 스크립트

`~/scripts/start-infra402.sh`:
```bash
#!/bin/bash
cd ~/git/infra402/backend-proxmox && uv run python main.py &
cd ~/git/infra402/backend-llm && uv run python pydantic-server.py &
cloudflared tunnel run infra402-api &
echo "All services started"
```

### 6.3 모니터링
- Cloudflare Dashboard에서 터널 상태 확인
- Vercel Dashboard에서 Frontend 로그 확인
- 로컬 터미널에서 Backend 로그 모니터링

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS Error | Backend CORS 설정에 Vercel 도메인 추가 |
| Tunnel Offline | cloudflared 프로세스 재시작, 인터넷 연결 확인 |
| Backend Not Responding | 포트 8000/4021 사용 중인지 확인 (`lsof -i :8000`) |
| Vercel Build Fail | Root Directory가 `frontend`인지 확인 |
