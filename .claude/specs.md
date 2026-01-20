# infra402 Deployment Specifications

## Architecture Overview

Mini PC (Proxmox) + Tailscale + Vercel

```
┌─────────────────────────────────────────────────────────────────┐
│  🌐 Internet                                                    │
│                                                                 │
│  👤 User  →  Vercel Frontend (infra402.vercel.app)             │
│                      │                                          │
│                      │ HTTPS                                    │
│                      ▼                                          │
│              Tailscale Funnel                                   │
│         (backend-service.tailXXX.ts.net)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Encrypted Tunnel
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  🖥️ Mini PC - Proxmox Host                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  LXC 100: backend-services                                │  │
│  │                                                           │  │
│  │  ┌─────────────────┐                                     │  │
│  │  │ Tailscale       │                                     │  │
│  │  │ Client          │                                     │  │
│  │  └────────┬────────┘                                     │  │
│  │           │                                               │  │
│  │           ▼                                               │  │
│  │  ┌─────────────────┐      ┌──────────────────┐          │  │
│  │  │ backend-llm     │─────→│ backend-proxmox  │          │  │
│  │  │ :8000           │      │ :4021            │          │  │
│  │  └─────────────────┘      └────────┬─────────┘          │  │
│  └───────────────────────────────────┼────────────────────┘  │
│                                       │                       │
│                                       ▼                       │
│                              ┌────────────────┐               │
│                              │ Proxmox API    │               │
│                              │ :8006          │               │
│                              └────────┬───────┘               │
│                                       │                       │
│                                       ▼                       │
│                              ┌────────────────┐               │
│                              │ User Containers│               │
│                              │ (Sandbox)      │               │
│                              └────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### LXC Container
| 항목 | 값 |
|------|-----|
| ID | 100 |
| Hostname | backend-services |
| CPU | 2 Cores |
| RAM | 2GB |
| Disk | 20GB |
| Features | nesting=1 (Tailscale 필수) |

### Services
| Service | Port | 용도 |
|---------|------|------|
| backend-llm | 8000 | LLM 챗봇 API |
| backend-proxmox | 4021 | 컨테이너 관리 API |

### Network
- **Tailscale Funnel**: `https://backend-service.tailXXXXX.ts.net`
- **Vercel**: `https://infra402.vercel.app`

---

## Environment Variables

### Backend-LLM
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
PRIVATE_KEY=0x...
BACKEND_BASE_URL=http://localhost:4021
```

### Backend-Proxmox
```env
ADDRESS=0x...
NETWORK=base-sepolia
PVE_HOST=https://localhost:8006
PVE_TOKEN_ID=root@pam!token
PVE_TOKEN_SECRET=...
PVE_NODE=pve
PVE_STORAGE=local-lvm
PVE_OS_TEMPLATE=local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

### Vercel
```env
VITE_CHAT_API_BASE=https://backend-service.tailXXXXX.ts.net
```

---

## Base App MiniApp Integration

### Overview
Frontend를 Farcaster Base App의 MiniApp으로 출시하여 Base 생태계에서 실행 가능하도록 합니다.

### 1. SDK Integration

**패키지 설치:**
```bash
pnpm add @farcaster/miniapp-sdk
```

**App.tsx 수정:**
```typescript
import { sdk } from '@farcaster/miniapp-sdk';
import { useEffect } from 'react';

function App() {
  useEffect(() => {
    sdk.actions.ready();  // 앱 로딩 완료 알림
  }, []);
  // ...
}
```

---

### 2. Manifest 파일 생성

**경로:** `public/.well-known/farcaster.json`

```json
{
  "accountAssociation": {
    "header": "",
    "payload": "",
    "signature": ""
  },
  "miniapp": {
    "version": "1",
    "name": "Infra402",
    "homeUrl": "https://infra402.vercel.app",
    "iconUrl": "https://infra402.vercel.app/icon.png",
    "splashImageUrl": "https://infra402.vercel.app/splash.png",
    "splashBackgroundColor": "#1a1a2e",
    "subtitle": "LXC Container Provisioning",
    "description": "Chat with an AI agent to provision LXC containers using x402 payments.",
    "primaryCategory": "developer_tools",
    "tags": ["infrastructure", "containers", "x402", "ai"],
    "tagline": "Provision containers with AI & x402"
  }
}
```

---

### 3. Embed Metadata 추가

**index.html `<head>` 섹션:**
```html
<meta name="fc:miniapp" content='{
  "version":"next",
  "imageUrl":"https://infra402.vercel.app/embed.png",
  "button":{
    "title":"Launch Infra402",
    "action":{
      "type":"launch_miniapp",
      "name":"Infra402",
      "url":"https://infra402.vercel.app"
    }
  }
}' />
```

---

### 4. Account Association (중요)

> **Ownership 주의:** 서명한 지갑이 앱의 소유자가 됩니다.

**절차:**
1. **전용 지갑 생성** (개인 지갑과 분리 권장)
2. [Base Build Tool](https://www.base.dev/preview?tab=account) 접속
3. 배포된 URL 입력: `infra402.vercel.app`
4. "Verify" 클릭 → 지갑 서명
5. 생성된 `header`, `payload`, `signature` 복사
6. `farcaster.json`의 `accountAssociation`에 값 입력

**예시:**
```json
{
  "accountAssociation": {
    "header": "eyJmaWQiOjEyMzQ1LCJ0eXBlIjoiY3VzdG9keSIsImtleSI6IjB4...",
    "payload": "eyJkb21haW4iOiJpbmZyYTQwMi52ZXJjZWwuYXBwIn0",
    "signature": "0x1234567890abcdef..."
  }
}
```

---

### 5. 배포 및 검증

**Vercel 재배포:**
```bash
git add .
git commit -m "feat: Add Base App MiniApp integration"
git push origin main
```

**검증:**
1. [Base Build Preview](https://www.base.dev/preview) 접속
2. URL 입력: `infra402.vercel.app`
3. 확인 항목:
   - ✅ Embed Preview (카드 표시)
   - ✅ Launch Button (앱 실행)
   - ✅ Account Association (서명 검증)
   - ✅ Metadata (모든 필드 표시)

---

### 6. 앱 퍼블리싱

**Base App에서:**
1. Base App (모바일) 열기
2. 새 포스트 작성
3. 앱 URL 포함: `https://infra402.vercel.app`
4. 게시

→ 앱이 Base App에 등록되고 사용자들이 발견 가능

---

### Troubleshooting

| 문제 | 해결 |
|------|------|
| SDK 오류 | `@farcaster/miniapp-sdk` 설치 확인 |
| Manifest 로드 실패 | `.well-known/farcaster.json` 경로 확인 |
| Account Association 실패 | 배포 URL과 서명 URL 일치 확인 |
| CORS 에러 | Vercel 도메인 허용 확인 |

---

### Reference
- [공식 마이그레이션 가이드](.claude/BASE_APP_MIGRATION_GUIDE.md)
- [Base Build Tool](https://www.base.dev/preview)
- [Farcaster Docs](https://docs.farcaster.xyz/)

