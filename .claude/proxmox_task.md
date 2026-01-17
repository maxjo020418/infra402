# Proxmox Deployment Tasks

## Checklist

- [ ] Step 1: CT 템플릿 다운로드
- [ ] Step 2: LXC 생성
- [ ] Step 3: 기본 환경 설정
- [ ] Step 4: Tailscale 설치
- [ ] Step 5: Backend 배포

---

## Step 1: CT 템플릿 다운로드

```bash
# Proxmox 호스트 Shell에서
pveam update
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

---

## Step 2: LXC 생성

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

---

## Step 3: 기본 환경 설정

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

## Step 4: Tailscale 설치

```bash
# Tailscale 설치
curl -fsSL https://tailscale.com/install.sh | sh

# 인증 (표시되는 URL로 브라우저에서 로그인)
tailscale up

# 상태 확인
tailscale status

# 공개 URL 생성 (8000 포트)
tailscale funnel 8000

# Funnel URL 확인
tailscale funnel status
```

---

## Step 5: Backend 배포

```bash
# 레포지토리 클론
cd /opt
git clone <your-repo-url> infra402
cd infra402

# backend-proxmox 환경변수
cd backend-proxmox
cp .example.env .env
nano .env  # PVE_HOST, PVE_TOKEN_ID 등 설정

# backend-llm 환경변수
cd ../backend-llm
cp .example.env .env
nano .env  # OPENAI_API_KEY, PRIVATE_KEY 등 설정

# 서비스 실행
cd /opt/infra402/backend-proxmox && uv sync && uv run python main.py &
cd /opt/infra402/backend-llm && uv sync && uv run python pydantic-server.py &
```

---

## Vercel 설정

Funnel URL 확인 후 Vercel Dashboard에서 환경변수 설정:
```
VITE_CHAT_API_BASE=https://backend-services.tailnet-xxxx.ts.net
```
