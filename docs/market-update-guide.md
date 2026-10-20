# 시장조사 업데이트 사용법

## 브라우저에서 기록
1. 공개 상품 페이지에서 상품번호, 색상·사이즈, 쿠폰 전 표시가를 확인합니다.
2. 시장조사 룸의 **가격 관찰 기록**에 실제 관찰일과 출처를 입력합니다.
3. **최근 확인 가격 반영** 모드를 선택해 반영 결과를 확인합니다.
4. **관찰 이력 백업**으로 JSON 파일을 보관합니다.

브라우저 입력은 현재 기기에만 저장됩니다. 공개 사이트 데이터가 자동으로 바뀌는 기능은 아닙니다.
동일 상품·옵션·가격 기준으로 다른 날짜가 2개 이상 있어야 가격 변화율을 계산합니다.
같은 날짜의 가격이 충돌하면 가져오기를 거부합니다. 시간을 구분하는 장중 가격 수집은 현재 지원하지 않습니다.

## 팀 공용 사이트에 반영
저장소를 내려받은 작업 폴더에서 Node.js로 실행합니다. 인증정보를 웹페이지에 입력하지 마세요.

```powershell
node docs/market-import.cjs "관찰이력백업.json" --check
node docs/market-import.cjs "관찰이력백업.json"
git diff -- docs/market-enrichment.json
git add docs/market-enrichment.json
git commit -m "data: add verified market observations"
git push
```

검증 실패·날짜 충돌이 있으면 저장하지 않습니다. 정상 저장 전 기존 파일은 work/market-backups/에 백업합니다. 이 폴더의 백업 파일은 공개 저장소에 올리지 않아도 됩니다.
원본 docs/data/market.json과 이전 상세 보고서는 변경하지 않습니다. GitHub Pages 배포 성공 후 공개 화면에서 관찰 이력을 확인합니다.
개발 도구 이용이 어렵다면 관찰 이력 백업 파일을 이 대화에 첨부해 공용 사이트 반영을 요청할 수 있습니다.

## 운영 기준
- 주 2회 정기 확인, 행사 기간은 매일 확인을 권장합니다. 실제 자동 예약 작업을 설정한 것은 아닙니다.
- 14일은 재조사 관리 기준입니다. 값이 정확하다고 보증하는 기간이 아닙니다.
- 원본 출처일·이미지 확보일·배포일을 가격 관찰일로 대신하지 않습니다.
- W컨셉의 기존 외부 출처가 끊긴 상품은 브랜드몰 이미지만 보완했습니다. 브랜드몰 가격을 W컨셉 가격으로 바꾸지 않습니다.
- 공개 이미지의 저작권은 원권리자에게 있으며, 연구용 원문 확인·저장 사실과 출처를 함께 표시합니다.
- 네이버 API, 플랫폼 피드, 팀 로그인·DB는 아직 연결되지 않았습니다. 인증정보·수집 권한이 확보되면 별도 개발해야 합니다.

## 참고한 공개 서비스 설명
- EDITED: 상품 구성, 가격, 프로모션 분석을 분리 https://edited.com/products/retail-intelligence-platform/
- Similarweb: 지표 범위·측정 기준·최신성 표시 https://support.similarweb.com/hc/en-us/articles/33639235837981-Retail-Intelligence-Metrics
- WGSN: 바잉 판단과 트렌드 근거 구분 https://www.wgsn.com/en/products/fashion-buying

유료 데이터나 예측값을 가져온 것이 아니라 기능 구성과 운영 원칙을 참고했습니다.
