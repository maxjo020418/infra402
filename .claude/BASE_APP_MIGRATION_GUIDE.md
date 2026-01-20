# Base App MiniApp Migration Agent Instructions

## Overview

이 문서는 기존 Web App을 Base App의 MiniApp으로 마이그레이션하기 위한 AI Agent 지침서입니다. 이 파일을 Agent에 첨부하면, Agent가 프로젝트를 Base App MiniApp으로 변환하는 작업을 수행합니다.

---

## Prerequisites

마이그레이션을 시작하기 전 다음 사항을 확인하세요:

- [ ] 기존 Web App 프로젝트가 존재함
- [ ] Base App 계정이 생성되어 있음
- [ ] 프로젝트가 배포 가능한 상태임 (Vercel, Netlify 등)

---

## Migration Steps

### Step 1: MiniApp SDK 설치

프로젝트의 패키지 매니저에 맞게 SDK를 설치합니다.

```bash
# npm
npm install @farcaster/miniapp-sdk

# pnpm
pnpm add @farcaster/miniapp-sdk

# yarn
yarn add @farcaster/miniapp-sdk
```

**Agent Action**: 프로젝트의 `package.json`을 확인하여 사용 중인 패키지 매니저를 파악하고 적절한 명령어를 실행하세요.

---

### Step 2: App Ready 트리거 구현

앱이 로드된 후 `sdk.actions.ready()`를 호출하여 로딩 스플래시 화면을 숨기고 앱을 표시합니다.

#### Vanilla JS

```javascript
// app.js
import { sdk } from '@farcaster/miniapp-sdk';

// 앱이 표시될 준비가 되면 호출
await sdk.actions.ready();
```

#### React

```tsx
// App.tsx
import { sdk } from '@farcaster/miniapp-sdk';
import { useEffect } from 'react';

function App() {
  useEffect(() => {
    sdk.actions.ready();
  }, []);

  return (
    // ...앱 컨텐츠
  );
}

export default App;
```

**Agent Action**:
1. 프로젝트가 React/Next.js인지 Vanilla JS인지 확인
2. 메인 엔트리 파일 (App.tsx, index.js 등)을 찾아 적절한 위치에 `sdk.actions.ready()` 호출 추가
3. React의 경우 `useEffect` 훅 내에서 호출하여 리렌더링마다 실행되지 않도록 처리

---

### Step 3: Manifest 파일 생성

`https://your-domain.com/.well-known/farcaster.json` 경로에 Manifest 파일을 생성합니다.

#### Vanilla JS / Static Sites

`/public/.well-known/farcaster.json` 파일 생성:

```json
{
  "accountAssociation": {
    "header": "",
    "payload": "",
    "signature": ""
  },
  "miniapp": {
    "version": "1",
    "name": "앱 이름",
    "homeUrl": "https://your-domain.com",
    "iconUrl": "https://your-domain.com/icon.png",
    "splashImageUrl": "https://your-domain.com/splash.png",
    "splashBackgroundColor": "#000000",
    "webhookUrl": "https://your-domain.com/api/webhook",
    "subtitle": "앱 부제목",
    "description": "앱에 대한 상세 설명",
    "screenshotUrls": [
      "https://your-domain.com/screenshot1.png",
      "https://your-domain.com/screenshot2.png",
      "https://your-domain.com/screenshot3.png"
    ],
    "primaryCategory": "social",
    "tags": ["tag1", "tag2", "tag3"],
    "heroImageUrl": "https://your-domain.com/hero.png",
    "tagline": "간단한 슬로건",
    "ogTitle": "OG 타이틀",
    "ogDescription": "OG 설명",
    "ogImageUrl": "https://your-domain.com/og.png",
    "noindex": false
  }
}
```

#### Next.js

`app/.well-known/farcaster.json/route.ts` 파일 생성:

```typescript
function withValidProperties(properties: Record<string, undefined | string | string[]>) {
  return Object.fromEntries(
    Object.entries(properties).filter(([_, value]) => (Array.isArray(value) ? value.length > 0 : !!value))
  );
}

export async function GET() {
  const URL = process.env.NEXT_PUBLIC_URL as string;

  return Response.json({
    accountAssociation: {
      header: "",
      payload: "",
      signature: ""
    },
    miniapp: withValidProperties({
      version: "1",
      name: "앱 이름",
      homeUrl: URL,
      iconUrl: `${URL}/icon.png`,
      splashImageUrl: `${URL}/splash.png`,
      splashBackgroundColor: "#000000",
      webhookUrl: `${URL}/api/webhook`,
      subtitle: "앱 부제목",
      description: "앱에 대한 상세 설명",
      screenshotUrls: [
        `${URL}/screenshot1.png`,
        `${URL}/screenshot2.png`,
        `${URL}/screenshot3.png`
      ],
      primaryCategory: "social",
      tags: ["tag1", "tag2", "tag3"],
      heroImageUrl: `${URL}/hero.png`,
      tagline: "간단한 슬로건",
      ogTitle: "OG 타이틀",
      ogDescription: "OG 설명",
      ogImageUrl: `${URL}/og.png`,
      noindex: false
    })
  });
}
```

**Agent Action**:
1. 프로젝트 구조에 맞는 Manifest 파일 위치 결정
2. 기존 프로젝트의 메타데이터 (package.json의 name, description 등)를 참조하여 필드 값 설정
3. URL은 배포 도메인으로 설정 (환경변수 활용 권장)

---

### Step 4: Account Association 생성

> **[USER ACTION REQUIRED - 외부 사이트 상호작용]**
>
> Account Association 자격 증명은 Base Build 웹사이트에서 생성해야 합니다.
>
> **수행 절차:**
> 1. 먼저 Manifest 파일이 포함된 상태로 앱을 배포하세요
> 2. 브라우저에서 [Base Build Account Association Tool](https://www.base.dev/preview?tab=account) 접속
> 3. `App URL` 필드에 배포된 도메인 입력 (예: `your-app.vercel.app`)
> 4. "Submit" 버튼 클릭
> 5. "Verify" 버튼 클릭 후 **지갑 서명** 진행
>    - Base App 계정과 연결된 지갑으로 서명 요청이 발생합니다
>    - 지갑 확장 프로그램 또는 모바일 지갑에서 서명을 승인하세요
> 6. 생성된 `header`, `payload`, `signature` 값을 복사
> 7. Agent에게 해당 값을 전달하여 Manifest 파일 업데이트 요청
>
> **Note**: Base Account로 서명하기 때문에 `signature` 필드가 일반 Farcaster custody wallet 서명보다 길어집니다.

**Agent Action**:
사용자가 Account Association 값을 제공하면 Manifest 파일의 `accountAssociation` 객체를 업데이트하세요:

```json
{
  "accountAssociation": {
    "header": "사용자가_제공한_header_값",
    "payload": "사용자가_제공한_payload_값",
    "signature": "사용자가_제공한_signature_값"
  },
  "miniapp": { ... }
}
```

---

### Step 5: Embed Metadata 추가

앱이 공유될 때 Rich Embed를 생성하기 위한 메타데이터를 추가합니다.

#### Vanilla JS / Static HTML

`index.html`의 `<head>` 섹션에 추가:

```html
<meta name="fc:miniapp" content='{
  "version": "next",
  "imageUrl": "https://your-domain.com/embed-image.png",
  "button": {
    "title": "Launch App",
    "action": {
      "type": "launch_miniapp",
      "name": "앱 이름",
      "url": "https://your-domain.com"
    }
  }
}' />
```

#### Next.js

`app/layout.tsx`에 메타데이터 생성 함수 추가:

```typescript
import { Metadata } from 'next';

export async function generateMetadata(): Promise<Metadata> {
  const URL = process.env.NEXT_PUBLIC_URL as string;

  return {
    other: {
      'fc:miniapp': JSON.stringify({
        version: 'next',
        imageUrl: `${URL}/embed-image.png`,
        button: {
          title: 'Launch App',
          action: {
            type: 'launch_miniapp',
            name: '앱 이름',
            url: URL,
            splashImageUrl: `${URL}/splash.png`,
            splashBackgroundColor: '#000000',
          },
        },
      }),
    },
  };
}
```

**Agent Action**:
1. 프로젝트 구조 확인 (React/Next.js vs Vanilla)
2. 적절한 위치에 fc:miniapp 메타 태그 추가
3. 기존 OG 태그가 있다면 함께 유지

---

### Step 6: 배포

변경사항을 Production에 배포합니다.

**Agent Action**:
1. 모든 변경사항이 커밋되었는지 확인
2. 배포 명령어 실행 또는 CI/CD 파이프라인 트리거 안내

---

### Step 7: Preview 및 검증

> **[USER ACTION REQUIRED - 외부 사이트 상호작용]**
>
> 배포 후 Base Build Preview Tool에서 앱을 검증해야 합니다.
>
> **수행 절차:**
> 1. 브라우저에서 [Base Build Preview Tool](https://www.base.dev/preview) 접속
> 2. 배포된 앱 URL 입력
> 3. 다음 항목 확인:
>    - **Embed Preview**: 앱 공유 시 표시되는 카드 확인
>    - **Launch Button**: 앱이 정상적으로 실행되는지 확인
>    - **Account Association Tab**: 자격 증명이 올바르게 생성되었는지 확인
>    - **Metadata Tab**: Manifest의 모든 필드가 올바르게 표시되는지 확인
>
> 문제가 발견되면 Agent에게 해당 내용을 전달하여 수정 요청하세요.

---

### Step 8: 앱 퍼블리싱

> **[USER ACTION REQUIRED - Base App에서 수행]**
>
> 최종적으로 Base App에 앱을 퍼블리싱합니다.
>
> **수행 절차:**
> 1. Base App (모바일 앱) 열기
> 2. 새 포스트 작성
> 3. 앱의 URL을 포스트에 포함하여 게시
> 4. 포스트가 게시되면 앱이 Base App에 등록됩니다

---

## Manifest Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `version` | Yes | 항상 "1" |
| `name` | Yes | 앱 이름 (최대 30자) |
| `homeUrl` | Yes | 앱의 메인 URL |
| `iconUrl` | Yes | 앱 아이콘 (200x200px 권장, PNG) |
| `splashImageUrl` | Yes | 스플래시 이미지 (200x200px 권장) |
| `splashBackgroundColor` | Yes | 스플래시 배경색 (HEX 코드) |
| `webhookUrl` | No | 웹훅 엔드포인트 URL |
| `subtitle` | No | 앱 부제목 (최대 50자) |
| `description` | No | 앱 설명 (최대 200자) |
| `screenshotUrls` | No | 스크린샷 URL 배열 (최대 5개) |
| `primaryCategory` | No | 주요 카테고리 |
| `tags` | No | 태그 배열 (최대 5개) |
| `heroImageUrl` | No | 히어로 이미지 URL |
| `tagline` | No | 짧은 슬로건 |
| `ogTitle` | No | Open Graph 타이틀 |
| `ogDescription` | No | Open Graph 설명 |
| `ogImageUrl` | No | Open Graph 이미지 |
| `noindex` | No | 검색 색인 제외 여부 |

---

## Troubleshooting

### SDK 관련 오류

```
Error: sdk is not defined
```
→ `@farcaster/miniapp-sdk` 패키지가 설치되었는지 확인

### Manifest 로드 실패

```
Failed to load manifest
```
→ `.well-known/farcaster.json` 경로 접근 가능 여부 확인
→ CORS 설정 확인

### Account Association 검증 실패

→ 배포된 URL과 서명 시 입력한 URL이 일치하는지 확인
→ Manifest가 최신 상태로 배포되었는지 확인

---

## Additional Resources

- [Base Build Preview Tool](https://www.base.dev/preview)
- [Base Build Account Association Tool](https://www.base.dev/preview?tab=account)
- [Base Documentation - llms.txt](https://docs.base.org/llms.txt)

---

## Agent Checklist

마이그레이션 완료 전 다음 항목을 확인하세요:

- [ ] `@farcaster/miniapp-sdk` 설치됨
- [ ] `sdk.actions.ready()` 호출 구현됨
- [ ] Manifest 파일 생성됨 (`.well-known/farcaster.json`)
- [ ] Account Association 값 입력됨 (사용자 제공)
- [ ] `fc:miniapp` 메타 태그 추가됨
- [ ] 앱 배포 완료
- [ ] Base Build Preview에서 검증 완료 (사용자 확인)
