# infra402 Deployment Plan

## Overview

Mini PC (Proxmox) + Tailscale + Vercel 배포 계획

---

## Prerequisites

### 필수 준비물

| 항목 | 확인 | 비고 |
|------|------|------|
| Proxmox Host | [ ] | Mini PC에 설치됨 |
| Tailscale 계정 | [ ] | [tailscale.com](https://tailscale.com) |
| Vercel 계정 | [ ] | [vercel.com](https://vercel.com) |
| OpenAI API Key | [ ] | LLM Provider (택1) |
| EVM Wallet Private Key | [ ] | x402 결제 서명용 |

---

## Phase 1: LXC 생성

### 1.1 CT 템플릿 다운로드
```bash
# Proxmox 호스트에서
pveam update
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

### 1.2 backend-services LXC 생성
```bash
pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname backend-services \
  --cores 2 \
  --memory 2048 \
  --swap 0 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --features nesting=1

pct start 100
```

### 1.3 기본 환경 설정
```bash
# LXC 접속
pct enter 100

# 시스템 업데이트
apt update && apt upgrade -y

# 필수 패키지 설치
apt install -y python3.11 python3-pip git curl

# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

---

## Phase 2: Tailscale 설치

### 2.1 Tailscale 설치
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

### 2.2 Tailscale 연결
```bash
# 인증 URL이 표시됨 → 브라우저에서 로그인
tailscale up

# 상태 확인
tailscale status
```

### 2.3 Tailscale Funnel 설정
```bash
# 8000 포트를 HTTPS로 공개
tailscale funnel 8000

# Funnel URL 확인 (예: https://backend-services.tailnet-xxxx.ts.net)
tailscale funnel status
```

---

## Phase 3: Backend 배포

### 3.1 레포지토리 클론
```bash
cd /opt
git clone https://github.com/your-repo/infra402.git
cd infra402
```

### 3.2 환경변수 설정
```bash
# backend-proxmox
cd /opt/infra402/backend-proxmox
cp .example.env .env
# nano .env → PVE_HOST, PVE_TOKEN_ID 등 설정

# backend-llm
cd /opt/infra402/backend-llm
cp .example.env .env
# nano .env → OPENAI_API_KEY, PRIVATE_KEY 등 설정
```

### 3.3 서비스 실행
```bash
# Terminal 1: backend-proxmox
cd /opt/infra402/backend-proxmox
uv sync
uv run python main.py  # :4021

# Terminal 2: backend-llm
cd /opt/infra402/backend-llm
uv sync
uv run python pydantic-server.py  # :8000
```

### 3.4 (선택) systemd 서비스 등록
```bash
# /etc/systemd/system/infra402.service
cat > /etc/systemd/system/infra402.service << 'EOF'
[Unit]
Description=infra402 Backend Services
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/infra402/backend-llm
ExecStart=/root/.local/bin/uv run python pydantic-server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable infra402
systemctl start infra402
```

---

## Phase 4: Vercel 연동

### 4.1 환경변수 설정

Vercel Dashboard → Settings → Environment Variables:
```
VITE_CHAT_API_BASE=https://backend-services.tailnet-xxxx.ts.net
```

### 4.2 배포 확인
1. Vercel에서 Frontend 재배포
2. 브라우저에서 접속 테스트
3. 개발자 도구 → Network에서 API 호출 확인

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tailscale 연결 안됨 | `tailscale up --reset` 후 재인증 |
| LXC에서 Tailscale 안됨 | `pct set 100 -features nesting=1` 확인 |
| Funnel URL 접근 안됨 | `tailscale funnel 8000` 재실행 |
| Backend 응답 없음 | `lsof -i :8000` 으로 포트 확인 |
