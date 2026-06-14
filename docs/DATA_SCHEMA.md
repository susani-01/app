# 데이터 스키마

조달청 나라장터 가격정보현황 OpenAPI에서 수집한 공공 데이터입니다. **데이터는 스타터에 포함되어 있지 않으니**, 아래에서 내려받아 `data/` 디렉터리에 두세요. (본인 구현의 `make setup`에서 이 다운로드를 자동화해도 됩니다.)

```bash
mkdir -p data
curl -o data/construction_classification.jsonl \
  https://storage.googleapis.com/timwork-hiring-data/construction-price/construction_classification.jsonl
curl -o data/std_market_price.jsonl \
  https://storage.googleapis.com/timwork-hiring-data/construction-price/std_market_price.jsonl
```

두 개의 JSONL 파일이며, 한 줄이 하나의 레코드(JSON 객체)에 대응됩니다.

## construction_classification.jsonl — 공종 분류 카탈로그

건설 공사를 공종(작업 종류)별로 분류한 마스터 데이터입니다.

| 필드 | 의미 | 예시 |
|---|---|---|
| `cnstwkDivCd` | 공종구분코드 | `A`, `C`, `E`, `M`, `R`, `T` |
| `cnstwkDivNm` | 공종구분명 | 건축공사 |
| `LvlqtyCalcCtyclCd1`~`5` | 분류 계층 코드 (5단계) | — |
| `LvlqtyCalcCtyclNm1`~`5` | 분류 계층 명칭 (5단계) | 공통공사 / 가설공사 / 임시시설 / … |
| `LvlqtyCalcCtyclDscrpt1`~`5` | 분류 계층 설명 (5단계) | — |
| `qtyCalcCtyclcd` | 수량산출항목코드 | `AAA161000000` |
| `qtyCalcCtyclNm` | 수량산출항목명 | 조립식가설울타리 |
| `spec` | 규격 | `H=2.0` |
| `unit` | 단위 | `m`, `㎡`, `개` |

- `LvlqtyCalcCtycl*1`~`*5`는 상위→하위 5단계 분류 계층입니다.
- `qtyCalcCtyclcd`는 계층 말단의 수량산출항목을 가리킵니다.

## std_market_price.jsonl — 표준시장단가

공종별 표준시장단가입니다.

| 필드 | 의미 | 예시 |
|---|---|---|
| `qtyCalcCtyclcd` | 수량산출항목코드 | `AAA162303500` |
| `cnstwkDivCd` | 공종구분코드 | `A` |
| `cnstwkDivCdNm` | 공종구분코드명 | 건축공사 |
| `prdnm` | 품명(작업명) | 가설울타리 설치 및 해체 |
| `spec` | 규격 | `EGI휀스/지주높이3.5m이하` |
| `unit` | 단위 | `m` |
| `mtrlcstUprc` | 재료비 단가 | `0` |
| `lbrcstUprc` | 노무비 단가 | `0` |
| `gnrexpnsUprc` | 경비 단가 | `25694` |
| `pblctDate` | 공시일자 | `20260527` |
| `uprcAplCndtnCntnts` | 단가적용조건내용 | 2026년도 하반기 표준시장단가 … |

## 참고

두 파일은 공공 OpenAPI에서 수집된 날것의 데이터로, 다음과 같이 정제되지 않은 부분이 있습니다.
- 같은 단위가 여러 형태로 표기됩니다. (예: `m`/`M`, `㎡`/`M2`/`m2`, `㎥`/`M3`/`m3`, 앞뒤 공백)
- `qtyCalcCtyclcd`가 비어 있는 행이 있습니다.
- 두 파일은 `qtyCalcCtyclcd`로 연결되는 것으로 보이며, 한쪽에만 존재하는 코드도 있습니다.
- 단가가 채워지지 않은 항목이 있습니다.
