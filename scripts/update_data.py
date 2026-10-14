#!/usr/bin/env python3
"""Headwear dashboard no-LLM data updater.

- Naver Shopping Search API (official API, credentials required)
- Authorized feed files for Musinsa, W Concept, 29CM, and KREAM
- No scraping, fake values, synthetic time-series or LLM calls
- Preserve original date and provenance; record new price history only on genuine fetch
"""
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs' / 'data' / 'market.json'
FEEDS = ROOT / 'feeds'
KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
TODAY = NOW.date().isoformat()
STAMP = NOW.isoformat(timespec='seconds')
PLATFORMS = ('무신사', 'W컨셉', '29CM', '크림', '네이버')
CATEGORIES = {'바라클라바', '트루퍼', '비니', '볼캡', '기타', '니트 후드'}
SEARCH_QUERIES = [('바라클라바 모자','바라클라바'), ('트루퍼 햇','트루퍼'), ('이어플랩 모자','트루퍼'), ('니트 비니','비니')]


def safe_url(url):
    return isinstance(url, str) and url.startswith('https://') and not url.lower().startswith('https://localhost')


def integer(value):
    try:
        i = int(value)
        return i if 0 <= i <= 100000000 else None
    except (ValueError, TypeError, OverflowError):
        return None


def clean_text(value):
    return html.unescape(re.sub('<[^>]+>', '', str(value or ''))).strip()[:190]


def request_naver(query):
    api_id = os.getenv('NAVER_CLIENT_ID', '')
    api_secret = os.getenv('NAVER_CLIENT_SECRET', '')
    if not (api_id and api_secret):
        raise RuntimeError('NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 미설정')
    params = urllib.parse.urlencode({'query': query, 'display': 12, 'sort': 'sim', 'exclude': 'used:rental:cbshop'})
    url = 'https://openapi.naver.com/v1/search/shop.json?' + params
    req = urllib.request.Request(url, headers={
        'X-Naver-Client-Id': api_id,
        'X-Naver-Client-Secret': api_secret,
        'User-Agent': 'HeadwearResearchDashboard/1.0',
        'Accept': 'application/json'
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode('utf-8'))


def naver_products():
    """Naver shopping search listing price is not necessarily final checkout price."""
    found = {}
    for query, category in SEARCH_QUERIES:
        result = request_naver(query)
        for x in result.get('items', []):
            price = integer(x.get('lprice'))
            url = x.get('link')
            pid = str(x.get('productId', '')).strip()
            title = clean_text(x.get('title'))
            if not (price and safe_url(url) and pid and title):
                continue
            if not any(w in title.replace(' ', '').lower() for w in ('바라클라바','트루퍼','이어플랩','비니','balaclava','trooper','beanie')):
                continue
            item = {
                'id': 'naver-' + re.sub('[^a-zA-Z0-9_-]', '', pid)[:60],
                'platform': '네이버', 'name': title,
                'brand': clean_text(x.get('brand') or x.get('mallName') or '브랜드 미기재'),
                'category': category, 'material': '미분류',
                'price': price, 'originalPrice': None, 'discountPct': None,
                'coupon': '네이버 쇼핑 검색 최저가 정보; 쿠폰/배송 미반영',
                'image': x.get('image') if safe_url(x.get('image')) else None,
                'imageProvenance': '네이버 쇼핑 검색 API 상품 이미지',
                'url': url, 'source': '네이버 공식 쇼핑 검색 API',
                'sourceDate': TODAY, 'observedAt': TODAY,
                'status': 'API 관찰', 'confidence': 'high',
                'rating': None, 'reviews': None, 'rank': None,
                'notes': '네이버 쇼핑 검색 API의 lprice; 몰별 실결제가가 아닌 참고 가격',
                'channel': '네이버 쇼핑', 'mallName': clean_text(x.get('mallName'))
            }
            found[item['id']] = item
    return list(found.values())


def authorized_feeds():
    """Consume only files supplied by authorized platform data provider.

    Format: {"platform": "29CM", "collectedAt": "2026-10-14", "products": [
      {"id":"sku_123", "name":"...", "price":49000, "url":"https://...", "brand":"...", "category":"트루퍼"}
    ]}
    """
    results = {}
    for filepath in sorted(FEEDS.glob('*.json')):
        try:
            raw = json.loads(filepath.read_text(encoding='utf-8'))
            platform = raw['platform']
            if platform == 'KREAM':
                platform = '크림'  # 과거 피드 호환
            observed = raw.get('collectedAt')
            if platform not in PLATFORMS or platform == '네이버':
                raise ValueError('피드 플랫폼 오류')
            if not isinstance(observed, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', observed):
                raise ValueError('실제 관찰 날짜(YYYY-MM-DD)가 필요합니다')
            if observed > TODAY:
                raise ValueError('미래 관찰일 기록 불가')
            parsed=[]
            for item in raw['products']:
                price=integer(item.get('price'))
                if price is None or not safe_url(item.get('url')) or not item.get('name') or not item.get('id'):
                    continue
                original=integer(item.get('originalPrice'))
                slug=re.sub('[^a-zA-Z0-9_-]', '', str(item['id']))[:75]
                if not slug:
                    continue
                parsed.append({
                    'id':f'{platform}-{slug}', 'platform':platform,'name':clean_text(item['name']),
                    'brand':clean_text(item.get('brand') or '브랜드 미기재'),
                    'category':item.get('category') if item.get('category') in CATEGORIES else '기타',
                    'material':clean_text(item.get('material') or '미분류'),
                    'price':price,'originalPrice':original,'discountPct':item.get('discountPct'),
                    'coupon':clean_text(item.get('coupon') or '상세 할인조건 미확인'),
                    'image':item.get('image') if safe_url(item.get('image')) else None,
                    'imageProvenance':'제공 피드', 'url':item['url'],
                    'source':clean_text(raw.get('provider') or '승인된 플랫폼 데이터 피드'),
                    'sourceDate':observed,'observedAt':observed,'status':'제공 피드 관찰',
                    'confidence':'high','rating':item.get('rating'),'reviews':item.get('reviews'),
                    'rank':None,'notes':clean_text(item.get('notes') or '제공 피드 표기 기준가'),
                    'channel':'제공 피드'
                })
            results.setdefault(platform, []).extend(parsed)
        except Exception as exc:
            print(f'WARN: feed {filepath.name}: {exc}', file=sys.stderr)
    return results


def update():
    db = json.loads(DATA.read_text(encoding='utf-8'))
    lookup={p['id']:p for p in db['products']}
    history=db.setdefault('history', [])
    changed=False
    imported={}
    if os.environ.get('NAVER_CLIENT_ID') and os.environ.get('NAVER_CLIENT_SECRET'):
        try:
            imported['네이버']=naver_products()
        except Exception as exc:
            print(f'WARN: Naver API failed; preserving previous data: {exc}',file=sys.stderr)
    else:
        print('INFO: Naver API credentials missing; existing data retained.')
    for key, values in authorized_feeds().items():
        imported.setdefault(key, []).extend(values)
    for platform, entries in imported.items():
        if not entries:
            continue
        successful=0
        for item in entries:
            old=lookup.get(item['id'])
            # Preserve previous fields not present in new observation, if any
            updated={**(old or {}),**item}
            if updated != old:
                lookup[item['id']]=updated
                changed=True
            hist={'id':item['id'],'platform':item['platform'],'observedAt':item['observedAt'],
                  'price':item['price'],'originalPrice':item['originalPrice'],'source':item['source'],'url':item['url']}
            key=(hist['id'],hist['observedAt'])
            old_index=next((i for i,h in enumerate(history) if (h.get('id'),h.get('observedAt'))==key),None)
            if old_index is None:
                history.append(hist)
                changed=True
            elif history[old_index]!=hist:
                history[old_index]=hist
                changed=True
            successful+=1
        if successful:
            observed_max=max((item['observedAt'] for item in entries),default=TODAY)
            for collector in db['collectors']:
                if collector['platform']==platform:
                    # Feed re-reading must not masquerade as a new observation.
                    newstate={'enabled':True,'lastSuccess':observed_max,
                              'detail':f'{successful}건 공급 기록 · 원자료 관찰일 {observed_max}'}
                    for key,val in newstate.items():
                        if collector.get(key)!=val:
                            collector[key]=val
                            changed=True
            print(f'INFO: {platform}: {successful} records imported')
    if changed:
        db['products']=list(lookup.values())
        # Bound observation history, keeping the most recent 180 days of dated samples
        cutoff=(NOW.date()-timedelta(days=180)).isoformat()
        db['history']=[h for h in history if h.get('observedAt','')>=cutoff]
        db['meta']['lastDataRefresh']=STAMP
        db['meta']['automation']='partially_active'
        DATA.write_text(json.dumps(db,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('INFO: Saved updated dataset.')
    else:
        print('INFO: No observations or data changes; keeping seed and last success time.')
    return changed

if __name__=='__main__':
    update()
