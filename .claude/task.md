# infra402 Deployment Tasks

> 현재 진행 상황을 추적합니다. 완료된 항목은 `[x]`, 진행 중은 `[/]`, 미완료는 `[ ]`로 표시합니다.

---

## Phase 1: Prerequisites 확인 ✅

- [x] Node.js 18+ 설치 확인 → v24.8.0
- [x] pnpm 설치 확인 → v10.23.0
- [x] Python 3.11+ 및 uv 설치 확인 → Python 3.13.2, uv 0.9.11
- [x] cloudflared 설치 확인 → v2025.11.1 (방금 설치)
- [x] Vercel 계정 준비
- [x] Cloudflare 계정 및 도메인 준비

---

## Phase 2: Backend 설정 ✅

- [x] backend-proxmox `.env` 파일 설정 → 나중에 추가 예정 (배포 테스트만 진행)
- [x] backend-llm `.env` 파일 설정 → Flock.io 설정 완료
- [x] CORS 설정 확인/수정 → 이미 `*` 허용됨
- [ ] backend-proxmox 로컬 실행 테스트 (:4021) → 나중에
- [x] backend-llm 로컬 실행 테스트 (:8000) → ✅ 성공

---

## Phase 3: Cloudflare Tunnel 설정 ✅

- [x] Quick Tunnel 사용 (도메인 없이 테스트용)
- [x] 터널 URL: `https://equipped-keen-disclose-starts.trycloudflare.com`
- [x] 터널 실행 및 연결 확인 → ✅ 성공
- [ ] (선택) 본인 도메인 구매 후 Named Tunnel로 전환

---

## Phase 4: Frontend Vercel 배포 ✅

- [x] Frontend `.env` 파일 설정 (VITE_CHAT_API_BASE) → 나중에 Tunnel URL로 설정
- [x] API URL 환경변수 사용 코드 확인/수정 → 이미 코드에 반영됨
- [x] 로컬 빌드 테스트 (`pnpm build`) → ✅ 성공
- [x] Vercel 프로젝트 생성 (Root Directory: frontend) → ✅ 완료
- [x] 환경변수 설정 (VITE_CHAT_API_BASE) → Quick Tunnel URL 설정 완료
- [x] 배포 완료 → https://infra402.vercel.app

---

## Phase 5: 통합 테스트 ✅

- [x] Backend API 외부 접근 테스트 → ✅ 성공
- [x] Frontend → Backend 연동 테스트 → ✅ 성공
- [x] CORS 동작 확인 → ✅ 정상
- [x] Chat 기능 End-to-End 테스트 → ✅ LLM 응답 확인

---

## Phase 6: 운영 안정화

- [ ] MacBook Sleep Mode 방지 설정
- [ ] Backend 자동 시작 스크립트 작성
- [ ] Cloudflare 터널 상태 모니터링 확인
- [ ] 장애 대응 절차 문서화

---

## Notes

> 작업 중 발생한 이슈나 메모를 여기에 기록합니다.

- ⚠️ Quick Tunnel URL은 재시작 시 변경됨. 나중에 본인 도메인 구매 권장.
- ✅ 2026-01-11 통합 테스트 성공
 
