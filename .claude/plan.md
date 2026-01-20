# infra402 Deployment Plan

## Overview

Mini PC (Proxmox) + Tailscale + Vercel 배포 계획

---

## Prerequisites

| 항목 | 비고 |
|------|------|
| Proxmox Host | Mini PC에 설치 |
| Tailscale 계정 | [tailscale.com](https://tailscale.com) |
| Vercel 계정 | [vercel.com](https://vercel.com) |
| OpenAI/Flock.io API Key | LLM Provider |
| EVM Wallet Private Key | x402 결제 서명용 |

---

## Phase 1: LXC 생성

### 1.1 CT 템플릿 다운로드
```bash
pveam update
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

### 1.2 backend-services LXC 생성
```bash
pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname backend-services \
  --cores 2 --memory 2048 --swap 0 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --features nesting=1

pct start 100
```

### 1.3 기본 환경 설정
```bash
pct enter 100
apt update && apt upgrade -y
apt install -y python3.11 python3-pip git curl
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

---

## Phase 2: Tailscale 설치

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
tailscale funnel 8000
tailscale funnel status  # URL 확인
```

---

## Phase 3: Backend 배포

```bash
cd /opt
git clone https://github.com/maxjo020418/infra402.git
cd infra402

# 환경변수 설정
cd backend-proxmox && cp .example.env .env && nano .env
cd ../backend-llm && cp .example.env .env && nano .env

# 실행
cd /opt/infra402/backend-proxmox && uv sync && uv run python main.py &
cd /opt/infra402/backend-llm && uv sync && uv run python pydantic-server.py &
```

---

## Phase 4: Vercel 연동

1. Vercel Dashboard → Settings → Environment Variables
2. `VITE_CHAT_API_BASE` = Tailscale Funnel URL
3. Redeploy

---

## Phase 5: Base App Migration

[상세 가이드](.claude/BASE_APP_MIGRATION_GUIDE.md)

### Quick Steps
1. `pnpm add @farcaster/miniapp-sdk`
2. `App.tsx`에 `sdk.actions.ready()` 추가
3. `public/.well-known/farcaster.json` 생성
4. [Base Build Tool](https://www.base.dev/preview?tab=account)에서 Account Association 서명
5. `index.html`에 `fc:miniapp` 메타 태그 추가
6. Vercel 재배포
