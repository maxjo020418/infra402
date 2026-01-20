# infra402 Deployment Tasks

> 현재 진행 상황을 추적합니다.

---

## Phase 1: Infrastructure Setup ✅

- [x] Proxmox LXC 생성 (backend-services)
- [x] Tailscale 설치 및 인증
- [x] Tailscale Funnel 설정 (:8000)
- [x] SSH 접근 설정

---

## Phase 2: Backend Deployment ✅

- [x] backend-proxmox 환경변수 설정
- [x] backend-llm 환경변수 설정 (Flock.io)
- [x] backend-proxmox 실행 (:4021)
- [x] backend-llm 실행 (:8000)
- [x] Tailscale Funnel URL 확인

---

## Phase 3: Frontend Deployment ✅

- [x] Vercel 프로젝트 생성
- [x] 환경변수 설정 (VITE_CHAT_API_BASE)
- [x] 배포 완료 (https://infra402.vercel.app)
- [x] End-to-End 테스트 성공

---

## Phase 4: Base App Migration ✅

- [x] SDK 설치 (@farcaster/miniapp-sdk)
- [x] App.tsx 수정 (sdk.actions.ready())
- [x] Manifest 생성 (farcaster.json)
- [x] Embed metadata (index.html)
- [ ] **Account Association** (User Action Required)

---

## Phase 5: Documentation ✅

- [x] .claude/ 폴더 추가
- [x] BASE_APP_MIGRATION_GUIDE.md 다운로드
- [x] plan.md, specs.md 최신화
- [x] 레포지토리 구조 정리

---

## Next Steps

1. **Account Association**: [Base Build Tool](https://www.base.dev/preview?tab=account)에서 전용 지갑으로 서명
2. **Manifest 업데이트**: farcaster.json에 서명 값 입력
3. **Vercel 재배포**: 변경사항 반영
