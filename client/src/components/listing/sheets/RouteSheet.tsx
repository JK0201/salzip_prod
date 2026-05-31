// 출퇴근 노선 상세 시트 — 카카오 길찾기 스타일 (BETA mock).
// ODSAY 다중 경로 검색 결과 흉내. 4개 경로 카드 순차 fade-in.
import { useEffect, useState } from 'react';
import { View, Text, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SheetShell } from './SheetShell';

const NEUTRAL = {
  ink: '#0A0A0B',
  ink2: '#18181B',
  text: '#27272A',
  textMute: '#71717A',
  border: '#E4E4E7',
  borderFaint: '#F4F4F5',
};

type LaneType = 'subway' | 'bus_trunk' | 'bus_branch' | 'bus_express' | 'bus_direct';

interface LaneChip {
  type: LaneType;
  name: string;
  // 지하철 호선 컬러용
  subwayLine?: '1' | '2' | '3' | '4' | '5' | '7' | '9' | 'bundang';
}

interface RouteCard {
  totalMin: number;
  walkMin: number;
  transfers: number;
  fareWon: number;
  distanceKm: number;
  origin: string;
  originType: 'bus' | 'subway';
  dest: string;
  destType: 'bus' | 'subway';
  lanes: LaneChip[];
  category: 'subway' | 'bus' | 'mixed';
}

// 지하철 호선 컬러 (카카오/네이버 기준)
const SUBWAY_COLOR: Record<NonNullable<LaneChip['subwayLine']>, string> = {
  '1': '#0052A4',
  '2': '#00A84D',
  '3': '#EF7C1C',
  '4': '#00A4E4',
  '5': '#996CAC',
  '7': '#747F00',
  '9': '#BDB092',
  'bundang': '#FABE00',
};

// 버스 카테고리 컬러
const BUS_COLOR: Record<Exclude<LaneType, 'subway'>, { bg: string; label: string }> = {
  bus_trunk:   { bg: '#2D69BD', label: '간선' },
  bus_branch:  { bg: '#5BBE45', label: '지선' },
  bus_express: { bg: '#E63329', label: '광역' },
  bus_direct:  { bg: '#FCC229', label: '직행' },
};

function chipStyle(chip: LaneChip): { bg: string; fg: string; prefix?: string } {
  if (chip.type === 'subway') {
    const c = SUBWAY_COLOR[chip.subwayLine ?? '2'];
    return { bg: c, fg: 'white' };
  }
  const c = BUS_COLOR[chip.type];
  return { bg: c.bg, fg: chip.type === 'bus_direct' ? '#0A0A0B' : 'white', prefix: c.label };
}

function buildMockRoutes(origin: string, destStation: string): RouteCard[] {
  return [
    {
      totalMin: 13, walkMin: 5, transfers: 0, fareWon: 1450, distanceKm: 1.7,
      origin: `${origin} 정류장`, originType: 'subway',
      dest: destStation, destType: 'subway',
      lanes: [{ type: 'subway', name: '2호선', subwayLine: '2' }],
      category: 'subway',
    },
    {
      totalMin: 15, walkMin: 8, transfers: 1, fareWon: 1650, distanceKm: 1.8,
      origin: `${origin} 정류장`, originType: 'bus',
      dest: destStation, destType: 'subway',
      lanes: [
        { type: 'bus_trunk', name: '360' },
        { type: 'subway', name: '2호선', subwayLine: '2' },
      ],
      category: 'mixed',
    },
    {
      totalMin: 18, walkMin: 12, transfers: 0, fareWon: 3000, distanceKm: 2.0,
      origin: `${origin} 정류장`, originType: 'bus',
      dest: `${destStation.replace('역', '')} 정류장`, destType: 'bus',
      lanes: [
        { type: 'bus_express', name: '9707' },
        { type: 'bus_direct', name: '1500' },
      ],
      category: 'bus',
    },
    {
      totalMin: 22, walkMin: 14, transfers: 1, fareWon: 1650, distanceKm: 2.4,
      origin: `${origin} 정류장`, originType: 'bus',
      dest: destStation, destType: 'subway',
      lanes: [
        { type: 'bus_branch', name: '4318' },
        { type: 'subway', name: '분당선', subwayLine: 'bundang' },
      ],
      category: 'mixed',
    },
  ];
}

const TABS = [
  { key: 'all',     label: '전체' },
  { key: 'bus',     label: '버스' },
  { key: 'subway',  label: '지하철' },
  { key: 'mixed',   label: '버스+지하철' },
] as const;
type TabKey = (typeof TABS)[number]['key'];

function LaneChipView({ chip }: { chip: LaneChip }) {
  const s = chipStyle(chip);
  return (
    <View style={{
      flexDirection: 'row', alignItems: 'center', gap: 4,
      backgroundColor: s.bg, borderRadius: 4, paddingHorizontal: 6, paddingVertical: 2,
    }}>
      {s.prefix && (
        <View style={{ backgroundColor: 'rgba(255,255,255,0.85)', paddingHorizontal: 3, borderRadius: 2 }}>
          <Text style={{ fontSize: 8, fontWeight: '800', color: s.bg }}>{s.prefix}</Text>
        </View>
      )}
      <Text style={{ fontSize: 11, fontWeight: '800', color: s.fg }}>{chip.name}</Text>
    </View>
  );
}

function StationDot({ type, color }: { type: 'bus' | 'subway'; color?: string }) {
  const c = color ?? (type === 'subway' ? '#0A0A0B' : '#71717A');
  return (
    <View style={{
      width: 18, height: 18, borderRadius: 9,
      backgroundColor: c, alignItems: 'center', justifyContent: 'center',
    }}>
      <Ionicons name={type === 'subway' ? 'subway-outline' : 'bus-outline'} size={10} color="white" />
    </View>
  );
}

function RouteCardView({ route }: { route: RouteCard }) {
  const firstChip = route.lanes[0];
  const firstColor = firstChip.type === 'subway'
    ? SUBWAY_COLOR[firstChip.subwayLine ?? '2']
    : BUS_COLOR[firstChip.type].bg;

  return (
    <View style={{
      backgroundColor: 'white', borderRadius: 12, padding: 14, marginBottom: 10,
      borderWidth: 1, borderColor: NEUTRAL.borderFaint,
    }}>
      {/* 헤더 — 시간·도보·환승·요금 */}
      <View style={{ flexDirection: 'row', alignItems: 'baseline', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
        <Text style={{ fontSize: 20, fontWeight: '800', color: NEUTRAL.ink, letterSpacing: -0.4 }}>
          {route.totalMin}분
        </Text>
        <Text style={{ fontSize: 11, color: NEUTRAL.textMute }}>
          도보 {route.walkMin}분
        </Text>
        <Text style={{ fontSize: 11, color: NEUTRAL.textMute }}>·</Text>
        <Text style={{ fontSize: 11, color: NEUTRAL.textMute }}>
          {route.transfers === 0 ? '환승없음' : `환승 ${route.transfers}회`}
        </Text>
        <Text style={{ fontSize: 11, color: NEUTRAL.textMute }}>·</Text>
        <Text style={{ fontSize: 11, color: NEUTRAL.textMute }}>
          {route.fareWon.toLocaleString()}원
        </Text>
        <Text style={{ fontSize: 11, color: NEUTRAL.textMute }}>·</Text>
        <Text style={{ fontSize: 11, color: NEUTRAL.textMute }}>
          {route.distanceKm}km
        </Text>
      </View>

      {/* 출발 정류장 + 노선 칩 + 도착 정류장 */}
      <View style={{ gap: 8 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <StationDot type={route.originType} color={firstColor} />
          <Text style={{ fontSize: 13, fontWeight: '700', color: NEUTRAL.ink, flex: 1 }} numberOfLines={1}>
            {route.origin}
          </Text>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, paddingLeft: 26 }}>
          {route.lanes.map((c, i) => (
            <View key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
              <LaneChipView chip={c} />
              {i < route.lanes.length - 1 && (
                <Ionicons name="chevron-forward" size={11} color={NEUTRAL.textMute} />
              )}
            </View>
          ))}
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <StationDot type={route.destType} color="#27272A" />
          <Text style={{ fontSize: 13, fontWeight: '700', color: NEUTRAL.ink, flex: 1 }} numberOfLines={1}>
            {route.dest}
          </Text>
        </View>
      </View>
    </View>
  );
}

export interface RouteSheetProps {
  visible: boolean;
  onClose: () => void;
  originArea: string;     // ex) "성수동"
  destLabel: string;      // ex) "강남역" or workplace
}

export function RouteSheet({ visible, onClose, originArea, destLabel }: RouteSheetProps) {
  const [tab, setTab] = useState<TabKey>('all');
  const [phase, setPhase] = useState<'searching' | 'ready'>('searching');

  useEffect(() => {
    if (!visible) { setPhase('searching'); return; }
    const t = setTimeout(() => setPhase('ready'), 900);
    return () => clearTimeout(t);
  }, [visible]);

  const all = buildMockRoutes(originArea, destLabel);
  const filtered = tab === 'all' ? all : all.filter((r) => r.category === tab);
  const counts = {
    all: all.length,
    bus: all.filter((r) => r.category === 'bus').length,
    subway: all.filter((r) => r.category === 'subway').length,
    mixed: all.filter((r) => r.category === 'mixed').length,
  };

  return (
    <SheetShell
      visible={visible}
      onClose={onClose}
      icon="bus-outline"
      title="출퇴근 노선 상세"
      sub={`${originArea} → ${destLabel}`}
      statusLabel={phase === 'searching' ? '경로 검색 중' : `${all.length}개 경로`}
      statusColor={phase === 'searching' ? '#0A0A0B' : '#047857'}
    >
      {/* 탭 */}
      <View style={{ flexDirection: 'row', gap: 0, marginBottom: 12, borderBottomWidth: 1, borderBottomColor: NEUTRAL.borderFaint }}>
        {TABS.map((t) => {
          const active = tab === t.key;
          return (
            <Pressable key={t.key} onPress={() => setTab(t.key)}
              style={{ flex: 1, paddingVertical: 10, alignItems: 'center',
                borderBottomWidth: active ? 2 : 0, borderBottomColor: '#0A0A0B' }}>
              <Text style={{
                fontSize: 12, fontWeight: active ? '800' : '600',
                color: active ? NEUTRAL.ink : NEUTRAL.textMute,
              }}>
                {t.label} {counts[t.key]}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {phase === 'searching' ? (
        <View style={{ padding: 32, alignItems: 'center', gap: 8 }}>
          <Ionicons name="navigate-circle-outline" size={32} color={NEUTRAL.textMute} />
          <Text style={{ fontSize: 12, color: NEUTRAL.textMute }}>대중교통 경로를 분석하고 있어요...</Text>
        </View>
      ) : filtered.length === 0 ? (
        <View style={{ padding: 32, alignItems: 'center' }}>
          <Text style={{ fontSize: 12, color: NEUTRAL.textMute }}>해당 유형의 경로가 없습니다.</Text>
        </View>
      ) : (
        filtered.map((r, i) => <RouteCardView key={i} route={r} />)
      )}
    </SheetShell>
  );
}
