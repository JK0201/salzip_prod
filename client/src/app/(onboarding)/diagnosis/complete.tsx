// Route: /(onboarding)/diagnosis/complete (S03: 맞춤 동네 결과)
import { useEffect, useMemo, useState } from 'react';
import { View, Text, Pressable, ScrollView, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MapHtmlView } from '@/components/MapHtmlView';
import { AppHeader } from '@/components/AppHeader';
import { TabBar } from '@/components/TabBar';
import { useDiagnosisStore } from '@/store/useDiagnosisStore';
import { listingThumb } from '@/constants/listingImages';
import { getLatestRecommend } from '@/api/recommend';
import type { Area, Listing } from '@/types/recommend';

const RANK_COLOR: Record<number, string> = {
  1: '#064E3B',
  2: '#059669',
  3: '#10B981',
  4: '#FCD34D',
  5: '#F59E0B',
};

function rankCol(rank: number): string {
  return RANK_COLOR[rank] ?? '#71717A';
}
function rankTxt(rank: number): string {
  return rank >= 4 ? '#064E3B' : 'white';
}

const KAKAO_JS_KEY = process.env.EXPO_PUBLIC_KAKAO_JS_KEY ?? '';
const LISTING_ZOOM_LEVEL = 4; // level ≤ 4면 전체 매물 자동 표시

function buildMapHTML(areas: Area[]): string {
  const geo = JSON.stringify(
    areas.map((a) => ({
      area_id: a.area_id,
      name: a.name,
      lat: a.lat,
      lng: a.lng,
      score: a.score,
      rank: a.rank,
    }))
  );
  const listingsByArea = JSON.stringify(
    areas.reduce<Record<string, Listing[]>>((acc, a) => {
      acc[a.area_id] = a.listings;
      return acc;
    }, {})
  );
  const centerLat = areas.length > 0 ? areas.reduce((s, a) => s + a.lat, 0) / areas.length : 37.552;
  const centerLng = areas.length > 0 ? areas.reduce((s, a) => s + a.lng, 0) / areas.length : 127.035;
  const rankColorJson = JSON.stringify(RANK_COLOR);

  return `<!DOCTYPE html>
<html>
<head>
<base href="https://localhost/">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<script>
(function(){
  var d=Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype,'src');
  var origCreate=document.createElement.bind(document);
  document.createElement=function(tag){
    var el=origCreate(tag);
    if(String(tag).toLowerCase()==='script'){
      Object.defineProperty(el,'src',{
        configurable:true,
        get:function(){return d.get.call(this);},
        set:function(v){
          if(typeof v==='string'){
            if(v.indexOf('http://')===0) v='https://'+v.slice(7);
            else if(v.indexOf('//')===0) v='https:'+v;
          }
          d.set.call(this,v);
        }
      });
    }
    return el;
  };
})();
</script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body,#map{width:100%;height:100%}
.mk{display:flex;flex-direction:column;align-items:center;cursor:pointer;transition:transform 0.2s cubic-bezier(.34,1.56,.64,1)}
.mk:hover{transform:scale(1.08)}
.mk-selected{transform:scale(1.18);z-index:10}
.mk-selected:hover{transform:scale(1.22)}
.mk-selected .bubble{box-shadow:0 5px 16px rgba(0,0,0,.4)}
.bubble{display:flex;flex-direction:row;align-items:center;gap:4px;padding:5px 10px;border-radius:20px;border:1.5px solid white;box-shadow:0 2px 8px rgba(0,0,0,.2);transition:box-shadow 0.2s}
.bubble-top{box-shadow:0 3px 14px rgba(0,0,0,.3)}
.b-score{font-weight:900;font-family:-apple-system,sans-serif;letter-spacing:-0.5px}
.b-name{font-weight:700;font-family:-apple-system,sans-serif}
.tail{width:0;height:0;border-style:solid}
.lk{display:flex;flex-direction:column;align-items:center;gap:3px;cursor:pointer;transition:transform 0.2s cubic-bezier(.34,1.56,.64,1);pointer-events:auto}
.lk:hover{transform:scale(1.08)}
.lk-selected{transform:scale(1.25);z-index:11}
.lk-selected:hover{transform:scale(1.28)}
.lk-selected .lk-lbl{box-shadow:0 4px 12px rgba(0,0,0,.35)}
.lk-dot{width:14px;height:14px;border-radius:7px;background:#2563EB;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,.35)}
.lk-lbl{background:#2563EB;color:white;padding:3px 8px;border-radius:11px;font-size:11px;font-weight:800;font-family:-apple-system,sans-serif;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,.25);border:1.5px solid white;letter-spacing:-0.2px;transition:box-shadow 0.2s}
.lk-flood .lk-dot{background:#DC2626}
.lk-flood .lk-lbl{background:#DC2626;color:white}
@keyframes pop{0%{opacity:0;transform:scale(0.3) translateY(10px)}65%{transform:scale(1.12) translateY(-3px)}100%{opacity:1;transform:scale(1) translateY(0)}}
@keyframes fadein{0%{opacity:0;transform:scale(0.7)}100%{opacity:1;transform:scale(1)}}
@keyframes fadeout{0%{opacity:1;transform:scale(1)}100%{opacity:0;transform:scale(0.7)}}
#hints{position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:10}
.hint{pointer-events:auto;display:flex;flex-direction:column;align-items:center;justify-content:center;position:absolute;width:40px;height:40px;cursor:pointer}
</style>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_JS_KEY}&autoload=false"></script>
</head>
<body>
<div id="map"></div>
<div id="hints"></div>
<script>
var GEO=${geo};
var LBA=${listingsByArea};
var RANK_COLOR=${rankColorJson};
var LISTING_ZOOM=${LISTING_ZOOM_LEVEL};

var selectedAreaId=null;
var selectedListingId=null;
var listingOverlays=[];
var listingMarkerEls={};
var listingOverlayById={};
var lastDrawnKey='';
var areaMarkerEls={};
var areaOverlays={};
var currentFilter={score:'전체',hasProperty:true,floodSafe:false};

// 부모(RN)→iframe 필터 메시지. SDK 로드 전 도착해도 currentFilter에 버퍼.
function receiveFilter(jsonStr){
  try{
    var d=typeof jsonStr==='string'?JSON.parse(jsonStr):jsonStr;
    if(d&&d.__cmd==='filter'){
      currentFilter=d.filter;
      if(window.__applyMapFilter) window.__applyMapFilter();
    }
  }catch(e){}
}
window.__deliver=receiveFilter;
window.addEventListener('message',function(e){ receiveFilter(e.data); });

function send(payload){
  var p=JSON.stringify(payload);
  if(window.ReactNativeWebView){window.ReactNativeWebView.postMessage(p);}
  else if(window.parent){window.parent.postMessage(p,'*');}
}

function rankColor(r){return RANK_COLOR[r]||'#71717A';}
function rankTxt(r){return r>=4?'#064E3B':'white';}

function fmtWan(v){
  if(v>=10000) return (v/10000).toFixed(v%10000===0?0:1)+'억';
  return v.toLocaleString()+'만';
}

kakao.maps.load(function(){
  var map=new kakao.maps.Map(document.getElementById('map'),{
    center:new kakao.maps.LatLng(${centerLat},${centerLng}),level:6
  });

  // 동 마커 그리기
  GEO.sort(function(a,b){return a.rank-b.rank;}).forEach(function(h,i){
    var col=rankColor(h.rank), txt=rankTxt(h.rank);
    var fs=h.rank===1?15:13;
    var wrap=document.createElement('div');
    wrap.className='mk';
    wrap.style.animation='pop 0.4s cubic-bezier(.34,1.56,.64,1) '+(i*0.12)+'s both';
    wrap.addEventListener('animationend',function(){this.style.animation='none';});
    wrap.onclick=function(e){
      e.stopPropagation();
      selectArea(h.area_id);
      send({type:'area',area_id:h.area_id});
    };
    var bubble=document.createElement('div');
    bubble.className='bubble';
    if(h.rank===1) bubble.classList.add('bubble-top');
    bubble.style.background=col;
    var sc=document.createElement('span');
    sc.className='b-score';
    sc.style.cssText='color:'+txt+';font-size:'+fs+'px';
    sc.textContent=String(h.score);
    var nm=document.createElement('span');
    nm.className='b-name';
    nm.style.cssText='color:'+txt+';font-size:'+(fs-2)+'px';
    nm.textContent=h.name;
    bubble.appendChild(sc);
    bubble.appendChild(nm);
    var tail=document.createElement('div');
    tail.className='tail';
    tail.style.cssText='border-width:7px 5px 0 5px;border-color:'+col+' transparent transparent transparent';
    wrap.appendChild(bubble);
    wrap.appendChild(tail);
    areaMarkerEls[h.area_id]=wrap;
    var aov=new kakao.maps.CustomOverlay({
      position:new kakao.maps.LatLng(h.lat,h.lng),
      content:wrap,xAnchor:.5,yAnchor:1,zIndex:5
    });
    aov.setMap(map);
    areaOverlays[h.area_id]=aov;
  });

  function listingsPassingFlood(aid){
    var items=LBA[aid]||[];
    if(currentFilter.floodSafe) items=items.filter(function(l){return !l.flood_risk;});
    return items;
  }

  function areaVisible(h){
    if(currentFilter.score==='80+' && h.score<80) return false;
    if(currentFilter.score==='70+' && h.score<70) return false;
    if(currentFilter.hasProperty && listingsPassingFlood(h.area_id).length===0) return false;
    return true;
  }

  function applyMapFilter(f){
    currentFilter=f;
    GEO.forEach(function(h){
      var ov=areaOverlays[h.area_id];
      if(ov) ov.setMap(areaVisible(h)?map:null);
    });
    if(selectedAreaId){
      var sel=GEO.find(function(g){return g.area_id===selectedAreaId;});
      if(sel && !areaVisible(sel)){
        selectedAreaId=null;
        updateAreaSelectionClass();
        clearListings();
        send({type:'clear'});
      } else if(map.getLevel()<6){
        // 줌인 상태에서만 매물 갱신. 줌아웃 상태면 hidden 유지.
        lastDrawnKey='__force';
        drawListings([selectedAreaId]);
      }
    }
    if(window.__updateHints) window.__updateHints();
  }

  // 맵 준비 완료 → 전역 훅 등록 + 버퍼된 필터 즉시 적용
  window.__applyMapFilter=function(){ applyMapFilter(currentFilter); };
  window.__applyMapFilter();

  function updateAreaSelectionClass(){
    Object.keys(areaMarkerEls).forEach(function(aid){
      var el=areaMarkerEls[aid];
      var ov=areaOverlays[aid];
      if(aid===selectedAreaId){
        el.classList.add('mk-selected');
        if(ov) ov.setZIndex(20);
      } else {
        el.classList.remove('mk-selected');
        if(ov) ov.setZIndex(5);
      }
    });
  }

  function clearListings(){
    if(lastDrawnKey===''){return;}
    listingOverlays.forEach(function(ov){ov.setMap(null);});
    listingOverlays=[];
    listingMarkerEls={};
    listingOverlayById={};
    lastDrawnKey='';
  }

  function selectListing(lid){
    selectedListingId=lid;
    Object.keys(listingMarkerEls).forEach(function(id){
      var el=listingMarkerEls[id];
      var ov=listingOverlayById[id];
      if(id===lid){
        el.classList.add('lk-selected');
        if(ov) ov.setZIndex(30);
      } else {
        el.classList.remove('lk-selected');
        if(ov) ov.setZIndex(10);
      }
    });
  }

  function drawListings(areaIds){
    var key=areaIds.slice().sort().join(',')+'|'+(currentFilter.floodSafe?'F':'');
    if(key===lastDrawnKey) return;
    lastDrawnKey=key;
    listingOverlays.forEach(function(ov){ov.setMap(null);});
    listingOverlays=[];
    listingMarkerEls={};
    listingOverlayById={};
    var total=0;
    areaIds.forEach(function(aid){
      var items=listingsPassingFlood(aid);
      total+=items.length;
      items.forEach(function(l,i){
        var el=document.createElement('div');
        el.className='lk';
        el.style.animation='fadein 0.3s ease '+(i*0.04)+'s both';
        el.addEventListener('animationend',function(){this.style.animation='none';});
        if(l.flood_risk) el.classList.add('lk-flood');
        var isSel=(l.id===selectedListingId);
        listingMarkerEls[l.id]=el;
        if(isSel) el.classList.add('lk-selected');
        el.onclick=function(e){
          e.stopPropagation();
          selectListing(l.id);
          send({type:'listing',listing_id:l.id,area_id:aid});
        };
        var dot=document.createElement('div');
        dot.className='lk-dot';
        var lbl=document.createElement('div');
        lbl.className='lk-lbl';
        lbl.textContent=fmtWan(l.deposit)+'/'+l.monthly_rent;
        el.appendChild(dot);
        el.appendChild(lbl);
        var ov=new kakao.maps.CustomOverlay({
          position:new kakao.maps.LatLng(l.lat,l.lng),
          content:el,xAnchor:.5,yAnchor:.5,zIndex:isSel?30:10
        });
        ov.setMap(map);
        listingOverlays.push(ov);
        listingOverlayById[l.id]=ov;
      });
    });
    console.log('[map] drawListings rendered',total,'markers');
  }

  function selectArea(aid){
    selectedAreaId=aid;
    updateAreaSelectionClass();
    var items=listingsPassingFlood(aid);
    console.log('[map] selectArea',aid,'listings:',items.length);
    var target=GEO.find(function(g){return g.area_id===aid;});
    if(target){
      // 동 중심 + 매물 좌표 centroid
      var pts=[[target.lat,target.lng]];
      items.forEach(function(l){pts.push([l.lat,l.lng]);});
      var cLat=0,cLng=0;
      pts.forEach(function(p){cLat+=p[0];cLng+=p[1];});
      cLat/=pts.length; cLng/=pts.length;
      // 적정 레벨 계산만 (즉시 원복)
      var prevLevel=map.getLevel();
      var bounds=new kakao.maps.LatLngBounds();
      pts.forEach(function(p){bounds.extend(new kakao.maps.LatLng(p[0],p[1]));});
      map.setBounds(bounds,50,50,50,50);
      var targetLevel=map.getLevel();
      map.setLevel(prevLevel);
      // 중심 즉시 이동 + 줌인만 애니메이션
      map.setCenter(new kakao.maps.LatLng(cLat,cLng));
      map.setLevel(targetLevel,{animate:{duration:350}});
    }
    drawListings([aid]);
  }

  // 줌아웃(level≥6) 매물 hidden, 줌인 복귀 시 선택 동 매물 재표시.
  // selectedAreaId는 유지 (toggle 아닌 hide 동작).
  kakao.maps.event.addListener(map,'zoom_changed',function(){
    if(map.getLevel()>=6){
      clearListings();
    } else if(selectedAreaId){
      drawListings([selectedAreaId]);
    }
  });

  /* ─── 화면 밖 동네 힌트 ─── */
  var SORTED=GEO.slice().sort(function(a,b){return a.rank-b.rank;});
  function edgePt(cx,cy,px,py,W,H,pad){
    var dx=px-cx,dy=py-cy;
    if(!dx&&!dy) return {x:cx,y:cy};
    var ts=[];
    if(dx>0)ts.push((W-pad-cx)/dx);
    if(dx<0)ts.push((pad-cx)/dx);
    if(dy>0)ts.push((H-pad-cy)/dy);
    if(dy<0)ts.push((pad-cy)/dy);
    var t=Math.min.apply(null,ts.filter(function(v){return v>0;}));
    return {x:Math.round(cx+dx*t),y:Math.round(cy+dy*t)};
  }
  function updateHints(){
    var hints=document.getElementById('hints');
    hints.innerHTML='';
    var proj=map.getProjection();
    var node=map.getNode();
    var W=node.clientWidth,H=node.clientHeight,pad=28,cx=W/2,cy=H/2;
    SORTED.forEach(function(h){
      if(!areaVisible(h)) return;
      var pt=proj.containerPointFromCoords(new kakao.maps.LatLng(h.lat,h.lng));
      var px=pt.x,py=pt.y;
      if(px>=pad&&px<=W-pad&&py>=pad&&py<=H-pad) return;
      var ep=edgePt(cx,cy,px,py,W,H,pad);
      var col=rankColor(h.rank),txt=rankTxt(h.rank);
      var ang=Math.atan2(py-cy,px-cx)*(180/Math.PI)+90;
      var el=document.createElement('div');
      el.className='hint';
      el.style.left=(ep.x-20)+'px';
      el.style.top=(ep.y-20)+'px';
      el.onclick=function(){selectArea(h.area_id);send({type:'area',area_id:h.area_id});};
      el.innerHTML='<div style="width:32px;height:32px;border-radius:50%;background:'+col+';border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.25);display:flex;align-items:center;justify-content:center;"><svg width="12" height="12" viewBox="0 0 12 12"><polygon points="6,1 11,11 6,8 1,11" fill="'+txt+'" transform="rotate('+ang+',6,6)"/></svg></div>';
      hints.appendChild(el);
    });
  }
  window.__updateHints=updateHints;
  kakao.maps.event.addListener(map,'idle',updateHints);
  kakao.maps.event.addListener(map,'zoom_start',function(){document.getElementById('hints').innerHTML='';});
  updateHints();
});
</script>
</body>
</html>`;
}

/* ─── KakaoMapView ─── */
function KakaoMapView({
  areas,
  filter,
  selectedArea,
  selectedListing,
  onSelectArea,
  onSelectListing,
  onClear,
  onShowList,
}: {
  areas: Area[];
  filter: FilterState;
  selectedArea: Area | null;
  selectedListing: { listing: Listing; area: Area } | null;
  onSelectArea: (a: Area) => void;
  onSelectListing: (l: Listing, a: Area) => void;
  onClear: () => void;
  onShowList: (area: Area) => void;
}) {
  const mapHtml = useMemo(() => buildMapHTML(areas), [areas]);
  const outbound = useMemo(
    () => JSON.stringify({ __cmd: 'filter', filter }),
    [filter]
  );

  const handleMessage = (data: string) => {
    try {
      const msg = JSON.parse(data) as
        | { type: 'area'; area_id: string }
        | { type: 'listing'; listing_id: string; area_id: string }
        | { type: 'clear' };
      if (msg.type === 'area') {
        const a = areas.find((x) => x.area_id === msg.area_id);
        if (a) onSelectArea(a);
      } else if (msg.type === 'listing') {
        const a = areas.find((x) => x.area_id === msg.area_id);
        const l = a?.listings.find((x) => x.id === msg.listing_id);
        if (a && l) onSelectListing(l, a);
      } else if (msg.type === 'clear') {
        onClear();
      }
    } catch {}
  };

  const floodCount =
    !filter.floodSafe && selectedArea
      ? selectedArea.listings.filter((l) => l.flood_risk).length
      : 0;

  return (
    <>
      <View
        style={{
          flex: 1,
          margin: 14,
          marginTop: 0,
          borderRadius: 12,
          overflow: 'hidden',
          borderWidth: 1,
          borderColor: '#F4F4F5',
        }}
      >
        <MapHtmlView html={mapHtml} onMessage={handleMessage} outbound={outbound} />
        {floodCount > 0 && (
          <View
            pointerEvents="none"
            style={{
              position: 'absolute',
              top: 10,
              right: 10,
              backgroundColor: '#FEF2F2',
              paddingHorizontal: 9,
              paddingVertical: 5,
              borderRadius: 8,
              flexDirection: 'row',
              alignItems: 'center',
              gap: 5,
              shadowColor: '#000',
              shadowOpacity: 0.1,
              shadowRadius: 4,
              elevation: 3,
              borderWidth: 1,
              borderColor: '#FECACA',
            }}
          >
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: '#DC2626' }} />
            <Text style={{ fontSize: 10, fontWeight: '800', color: '#DC2626' }}>
              침수 매물 {floodCount}건
            </Text>
          </View>
        )}
      </View>
      {selectedListing ? (
        <ListingCard
          listing={selectedListing.listing}
          area={selectedListing.area}
          onPress={() => router.push(`/listing/${selectedListing.listing.id}` as never)}
        />
      ) : (selectedArea ?? areas[0]) ? (
        <AreaCard area={selectedArea ?? areas[0]} onPress={() => onShowList(selectedArea ?? areas[0])} />
      ) : null}
    </>
  );
}

function AreaCard({ area, onPress }: { area: Area; onPress: () => void }) {
  return (
    <View
      className="flex-row items-center gap-2.5 mx-[14px] mb-[14px] bg-white rounded-2xl p-3"
      style={{ shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, elevation: 4 }}
    >
      <View
        style={{
          width: 36,
          height: 36,
          borderRadius: 18,
          backgroundColor: rankCol(area.rank),
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Text style={{ color: rankTxt(area.rank), fontWeight: '800', fontSize: 14, letterSpacing: -0.3 }}>
          {area.score}
        </Text>
      </View>
      <View className="flex-1">
        <Text className="text-[12px] font-extrabold text-[#0A0A0B] tracking-[-0.12px]">{area.name}</Text>
        <Text className="text-[10px] text-[#71717A]">
          {area.meta.split(' · ')[0]} · 매물 {area.listings.length}건 · 통근 약 {area.commuteMinutes}분
        </Text>
      </View>
      <Pressable
        onPress={onPress}
        style={{ width: 28, height: 28, backgroundColor: '#0A0A0B', borderRadius: 6, alignItems: 'center', justifyContent: 'center' }}
      >
        <Ionicons name="list-outline" size={14} color="white" />
      </Pressable>
    </View>
  );
}

function ListingCard({
  listing,
  area,
  onPress,
}: {
  listing: Listing;
  area: Area;
  onPress: () => void;
}) {
  const depositLabel = listing.deposit >= 10000
    ? `${(listing.deposit / 10000).toFixed(listing.deposit % 10000 === 0 ? 0 : 1)}억`
    : `${listing.deposit.toLocaleString()}만`;
  return (
    <Pressable
      onPress={onPress}
      className="flex-row items-center gap-2.5 mx-[14px] mb-[14px] bg-white rounded-2xl p-3 active:opacity-80"
      style={{ shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, elevation: 4 }}
    >
      <View style={{ width: 36, height: 36, borderRadius: 8, overflow: 'hidden', backgroundColor: '#F4F4F5' }}>
        <Image source={listingThumb(listing.id)} style={{ width: 36, height: 36 }} resizeMode="cover" />
      </View>
      <View className="flex-1">
        <Text className="text-[12px] font-extrabold text-[#0A0A0B] tracking-[-0.12px]" numberOfLines={1}>
          {listing.building_name ?? area.name + ' ' + (listing.estimated_kind ?? listing.kind)}
        </Text>
        <Text className="text-[10px] text-[#71717A]" numberOfLines={1}>
          {depositLabel}/{listing.monthly_rent}만 · {listing.area_m2 ?? '?'}㎡
          {listing.floor !== null ? ` · ${listing.floor}층` : ''}
          {listing.flood_risk ? ' · 침수 주의' : ''}
        </Text>
      </View>
      <View
        style={{
          width: 28,
          height: 28,
          backgroundColor: '#0A0A0B',
          borderRadius: 6,
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Ionicons name="chevron-forward" size={12} color="white" />
      </View>
    </Pressable>
  );
}

/* ─── ListCard (리스트 탭 — 동네 1개, 탭하면 검색으로) ─── */
function ListCard({ area }: { area: Area }) {
  const isTop = area.rank === 1;
  return (
    <View
      style={{
        borderWidth: 1,
        borderColor: '#E4E4E7',
        borderRadius: 12,
        padding: 12,
        gap: 8,
        backgroundColor: 'white',
      }}
    >
      <Pressable
        className="gap-2 active:opacity-70"
        onPress={() => router.push(`/search?areaId=${area.area_id}` as never)}
      >
        <View className="flex-row items-center gap-2.5">
          <View
            style={{
              width: 32,
              height: 32,
              borderRadius: 16,
              backgroundColor: rankCol(area.rank),
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Text style={{ color: rankTxt(area.rank), fontWeight: '800', fontSize: 12, letterSpacing: -0.2 }}>
              {area.score}
            </Text>
          </View>
          <View className="flex-1">
            <Text className="text-[13px] font-extrabold text-[#0A0A0B] tracking-[-0.13px]">{area.name}</Text>
            <Text className="text-[10px] text-[#71717A]">
              {area.meta.split(' · ')[0]} · 매물 {area.listings.length}건 · 통근 약 {area.commuteMinutes}분
            </Text>
          </View>
          {isTop && (
            <View className="px-1.5 py-0.5 bg-[#FAFAFA] rounded">
              <Text className="text-[9px] font-bold text-[#3F3F46]">TOP</Text>
            </View>
          )}
          <Ionicons name="chevron-forward" size={16} color="#A1A1AA" />
        </View>

        <View className="flex-row gap-1.5">
          {(
            [
              ['직장', area.scores.work],
              ['라이프', area.scores.life],
              ['안전', area.scores.safe],
            ] as [string, number][]
          ).map(([label, val]) => (
            <View key={label} className="flex-1 gap-[3px]">
              <Text className="text-[9px] text-[#71717A] font-semibold">{label}</Text>
              <View className="h-[3px] bg-[#E4E4E7] rounded-full overflow-hidden">
                <View className="h-full bg-[#0A0A0B] rounded-full" style={{ width: `${val}%` }} />
              </View>
              <Text className="text-[11px] font-extrabold text-[#0A0A0B] tracking-[-0.2px]">{val}</Text>
            </View>
          ))}
        </View>
      </Pressable>
    </View>
  );
}

/* ─── EmptyState ─── */
function EmptyState() {
  return (
    <View className="flex-1 items-center justify-center px-5 gap-4">
      <View
        style={{
          width: 88,
          height: 88,
          borderRadius: 44,
          backgroundColor: '#FAFAFA',
          borderWidth: 1,
          borderColor: '#E4E4E7',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Ionicons name="search-outline" size={36} color="#A1A1AA" />
      </View>
      <View className="items-center gap-1">
        <Text className="text-[15px] font-extrabold text-[#0A0A0B] tracking-[-0.15px] text-center">
          맞춤 동네를{'\n'}찾지 못했어요
        </Text>
        <Text className="text-[11px] text-[#71717A] text-center leading-[1.5]">
          조건이 너무 좁아서 매칭이 되지 않았어요.{'\n'}몇 가지를 완화하면 결과를 받을 수 있어요.
        </Text>
      </View>
      <Pressable
        className="w-full bg-[#0A0A0B] rounded-xl py-4 flex-row items-center justify-center gap-1.5 active:opacity-75"
        onPress={() => router.replace('/(onboarding)/start')}
      >
        <Text className="text-[12px] font-bold text-white">조건 다시 진단하기</Text>
        <Ionicons name="arrow-forward" size={12} color="white" />
      </Pressable>
    </View>
  );
}

/* ─── FilterSheet ─── */
const SORT_OPTIONS = ['매칭 점수 ↓', '통근 시간 ↑', '안전도 ↓'] as const;
const SCORE_OPTIONS = ['전체', '80+', '70+'] as const;

type SortOption = (typeof SORT_OPTIONS)[number];
type ScoreOption = (typeof SCORE_OPTIONS)[number];

type FilterState = {
  sort: SortOption;
  score: ScoreOption;
  hasProperty: boolean;
  floodSafe: boolean;
};

const FILTER_DEFAULT: FilterState = {
  sort: '매칭 점수 ↓',
  score: '전체',
  hasProperty: true,
  floodSafe: false,
};

export function applyFilter(areas: Area[], f: FilterState): Area[] {
  let out = areas.slice();
  if (f.score === '80+') out = out.filter((a) => a.score >= 80);
  else if (f.score === '70+') out = out.filter((a) => a.score >= 70);
  if (f.hasProperty) out = out.filter((a) => a.listings.length > 0);
  if (f.floodSafe) {
    out = out.map((a) => ({ ...a, listings: a.listings.filter((l) => !l.flood_risk) }));
  }
  if (f.sort === '매칭 점수 ↓') out.sort((a, b) => b.score - a.score);
  else if (f.sort === '통근 시간 ↑') out.sort((a, b) => a.commuteMinutes - b.commuteMinutes);
  else if (f.sort === '안전도 ↓') out.sort((a, b) => b.scores.safe - a.scores.safe);
  return out;
}

function FilterToggle({ on, onPress }: { on: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      style={{ width: 28, height: 16, borderRadius: 8, backgroundColor: on ? '#0A0A0B' : '#D4D4D8', justifyContent: 'center' }}
    >
      <View style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: 'white', position: 'absolute', left: on ? 14 : 2 }} />
    </Pressable>
  );
}

function FilterSheet({
  current,
  onApply,
  onClose,
  view,
}: {
  current: FilterState;
  onApply: (f: FilterState) => void;
  onClose: () => void;
  view: 'map' | 'list';
}) {
  const [draft, setDraft] = useState<FilterState>(current);

  const reset = () => setDraft(FILTER_DEFAULT);
  const commit = () => {
    onApply(draft);
    onClose();
  };

  return (
    <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 20 }}>
      <Pressable style={{ flex: 1, backgroundColor: 'rgba(10,10,11,0.45)' }} onPress={onClose} />
      <View
        style={{
          backgroundColor: 'white',
          borderTopLeftRadius: 20,
          borderTopRightRadius: 20,
          padding: 16,
          paddingBottom: 28,
          shadowColor: '#000',
          shadowOpacity: 0.2,
          shadowRadius: 20,
          elevation: 10,
        }}
      >
        <View style={{ width: 36, height: 4, borderRadius: 2, backgroundColor: '#D4D4D8', alignSelf: 'center', marginBottom: 12 }} />
        <Text className="text-[15px] font-extrabold text-[#0A0A0B] tracking-[-0.15px] mb-[14px]">
          {view === 'list' ? '정렬 · 필터' : '필터'}
        </Text>

        {view === 'list' && (
          <>
            <Text className="text-[10px] font-bold text-[#3F3F46] tracking-[0.02em] mb-1.5">정렬</Text>
            <View className="flex-row flex-wrap gap-1 mb-4">
              {SORT_OPTIONS.map((o) => (
                <Pressable
                  key={o}
                  onPress={() => setDraft({ ...draft, sort: o })}
                  className={`px-2.5 py-[5px] rounded-full border ${draft.sort === o ? 'bg-[#0A0A0B] border-[#0A0A0B]' : 'bg-white border-[#E4E4E7]'}`}
                >
                  <Text className={`text-[10px] font-semibold ${draft.sort === o ? 'text-white' : 'text-[#3F3F46]'}`}>{o}</Text>
                </Pressable>
              ))}
            </View>
          </>
        )}

        <Text className="text-[10px] font-bold text-[#3F3F46] tracking-[0.02em] mb-1.5">매칭 점수</Text>
        <View className="flex-row gap-1 mb-4">
          {SCORE_OPTIONS.map((o) => (
            <Pressable
              key={o}
              onPress={() => setDraft({ ...draft, score: o })}
              className={`px-2.5 py-[5px] rounded-full border ${draft.score === o ? 'bg-[#0A0A0B] border-[#0A0A0B]' : 'bg-white border-[#E4E4E7]'}`}
            >
              <Text className={`text-[10px] font-semibold ${draft.score === o ? 'text-white' : 'text-[#3F3F46]'}`}>{o}</Text>
            </Pressable>
          ))}
        </View>

        {(
          [
            ['매물 보유 동네만', draft.hasProperty, () => setDraft({ ...draft, hasProperty: !draft.hasProperty })],
            ['침수 매물 제외', draft.floodSafe, () => setDraft({ ...draft, floodSafe: !draft.floodSafe })],
          ] as [string, boolean, () => void][]
        ).map(([label, on, fn]) => (
          <View key={label} className="flex-row items-center justify-between py-2 border-t border-[#F4F4F5]">
            <Text className="text-[11px] font-semibold text-[#18181B]">{label}</Text>
            <FilterToggle on={on} onPress={fn} />
          </View>
        ))}

        <View className="flex-row gap-2 mt-3">
          <Pressable className="flex-1 py-[11px] rounded-xl border border-[#D4D4D8] items-center active:opacity-70" onPress={reset}>
            <Text className="text-[12px] font-bold text-[#18181B]">초기화</Text>
          </Pressable>
          <Pressable className="flex-1 py-[11px] rounded-xl bg-[#0A0A0B] items-center active:opacity-75" onPress={commit}>
            <Text className="text-[12px] font-bold text-white">적용하기</Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

/* ─── ViewToggle ─── */
function ViewToggle({ view, onChange }: { view: 'map' | 'list'; onChange: (v: 'map' | 'list') => void }) {
  return (
    <View className="flex-row bg-[#FAFAFA] rounded-full p-[3px] gap-0.5 self-start ml-[14px] mt-3 mb-2">
      {(['map', 'list'] as const).map((v) => (
        <Pressable
          key={v}
          onPress={() => onChange(v)}
          className={`flex-row items-center gap-1 px-[11px] py-[5px] rounded-full ${view === v ? 'bg-white' : ''}`}
          style={view === v ? { shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 2, elevation: 2 } : {}}
        >
          <Ionicons name={v === 'map' ? 'map-outline' : 'list-outline'} size={11} color={view === v ? '#0A0A0B' : '#71717A'} />
          <Text style={{ fontSize: 10, fontWeight: view === v ? '700' : '600', color: view === v ? '#0A0A0B' : '#71717A' }}>
            {v === 'map' ? '지도' : '리스트'}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

/* ─── Main Screen ─── */
export default function CompleteScreen() {
  const { results, matchId, setResults } = useDiagnosisStore();
  const [restoring, setRestoring] = useState(false);

  // 새로고침/재진입 = store 휘발 → 세션 기반 최근 추천 복원
  useEffect(() => {
    if (results.length === 0) {
      setRestoring(true);
      getLatestRecommend()
        .then((res) => {
          if (res.areas?.length) setResults(res.areas, res.match_id);
          // 라이프스타일 태그도 복원
          const names = (res.request as { lifestyle_tags?: string[] } | undefined)?.lifestyle_tags;
          if (names && names.length > 0) {
            useDiagnosisStore.setState({
              lifestyleTags: names.map((n) => ({ id: n, name: n })),
            });
          }
        })
        .catch((e) => console.log('[complete] restore error', e?.response?.status))
        .finally(() => setRestoring(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const view = useDiagnosisStore((s) => s.resultView);
  const setView = useDiagnosisStore((s) => s.setResultView);
  const [selectedArea, setSelectedArea] = useState<Area | null>(null);
  const [selectedListing, setSelectedListing] = useState<{ listing: Listing; area: Area } | null>(null);
  const [filter, setFilter] = useState<FilterState>(FILTER_DEFAULT);
  const [showFilter, setShowFilter] = useState(false);
  // 리스트 뷰 + 카운트용 (RN 측 필터). 지도 뷰는 HTML 내부에서 필터 (재로드 X).
  const areasForList = useMemo(() => applyFilter(results, filter), [results, filter]);

  const isEmpty = results.length === 0 && !restoring;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
      <AppHeader title="맞춤 동네 결과" onAction={() => setShowFilter(true)} />

      {isEmpty ? (
        <EmptyState />
      ) : (
        <View style={{ flex: 1 }}>
          <ViewToggle view={view} onChange={setView} />

          {view === 'map' ? (
            <KakaoMapView
              areas={results}
              filter={filter}
              selectedArea={selectedArea}
              selectedListing={selectedListing}
              onSelectArea={(a) => {
                setSelectedArea(a);
                setSelectedListing(null);
              }}
              onSelectListing={(l, a) => setSelectedListing({ listing: l, area: a })}
              onClear={() => {
                setSelectedArea(null);
                setSelectedListing(null);
              }}
              onShowList={(a) => {
                router.push(`/search?areaId=${a.area_id}` as never);
              }}
            />
          ) : (
            <ScrollView
              className="flex-1 px-[14px]"
              contentContainerStyle={{ gap: 8, paddingBottom: 14 }}
              showsVerticalScrollIndicator={false}
            >
              {areasForList.map((a) => (
                <ListCard key={a.area_id} area={a} />
              ))}
            </ScrollView>
          )}
        </View>
      )}

      <TabBar />

      {showFilter && (
        <FilterSheet
          current={filter}
          onApply={setFilter}
          onClose={() => setShowFilter(false)}
          view={view}
        />
      )}
    </SafeAreaView>
  );
}
