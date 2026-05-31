// Route: /(main)/search (S05: 매물 리스트)
import { TabBar } from '@/components/TabBar';
import { listingThumb } from '@/constants/listingImages';
import { useDiagnosisStore } from '@/store/useDiagnosisStore';
import { useFavoriteStore } from '@/store/useFavoriteStore';
import { getLatestRecommend } from '@/api/recommend';
import type { Area, Listing as RecListing } from '@/types/recommend';
import { Ionicons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { FlatList, Image, Pressable, ScrollView, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

/* ─── 타입 ─── */
type BadgeVariant = 'safe' | 'mid' | 'danger' | 'hug' | 'budget' | 'year';

type Listing = {
  id: string;
  name: string | null;
  kind: string;
  isNew: boolean;
  isSaved: boolean;
  isRecommended: boolean;
  matchPct?: number;
  deposit: string;
  monthly: string;
  area: string;
  floor: string;
  photoCount: number;
  badges: { variant: BadgeVariant; label: string }[];
};

/* ─── 매물 포맷 헬퍼 ─── */
function fmtMan(v: number): string {
  return v >= 10000 ? `${(v / 10000).toFixed(v % 10000 === 0 ? 0 : 1)}억` : `${v.toLocaleString()}만`;
}

// recommend 응답의 매물(RecListing) → 카드용 Listing. 사진/호수는 데이터 없어 목 유지.
function toCard(l: RecListing, area: Area, rank: number): Listing {
  const flood = l.flood_risk === true;
  const badges: { variant: BadgeVariant; label: string }[] = [
    flood ? { variant: 'danger', label: '침수 이력' } : { variant: 'safe', label: '안전' },
  ];
  if (l.build_year != null) badges.push({ variant: 'year', label: `${l.build_year}년` });
  return {
    id: l.id,
    name: l.building_name,
    kind: l.estimated_kind ?? l.kind,
    isNew: false,
    isSaved: false,
    isRecommended: rank === 0,
    matchPct: rank === 0 ? area.score : undefined,
    deposit: fmtMan(l.deposit),
    monthly: l.monthly_rent > 0 ? `${l.monthly_rent}만` : '전세',
    area: l.area_m2 != null ? `${l.area_m2}㎡` : '-',
    floor: l.floor != null ? `${l.floor}층` : '-',
    photoCount: 8, // 목: 실거래가 데이터에 사진 없음
    badges,
  };
}

const BADGE_STYLE: Record<BadgeVariant, { bg: string; text: string }> = {
  safe:   { bg: '#ECFDF5', text: '#047857' },
  mid:    { bg: '#FEF3C7', text: '#B45309' },
  danger: { bg: '#FEE2E2', text: '#B91C1C' },
  hug:    { bg: '#EFF6FF', text: '#1D4ED8' },
  budget: { bg: '#D1FAE5', text: '#047857' },
  year:   { bg: '#EFF6FF', text: '#1D4ED8' },
};

/* ─── ListingCard ─── */
function ListingCard({ item, onToggleSave }: { item: Listing; onToggleSave: (id: string) => void }) {
  const { bg: recBg, border: recBorder } = item.isRecommended
    ? { bg: '#F0FDF9', border: '#10B981' }
    : { bg: '#FFFFFF', border: '#E4E4E7' };

  return (
    <Pressable onPress={() => router.push(`/listing/${item.id}` as never)}
      style={{ borderWidth: item.isRecommended ? 1.5 : 1, borderColor: recBorder,
        borderRadius: 14, backgroundColor: recBg, overflow: 'visible', marginTop: item.isRecommended ? 10 : 0 }}>
      {item.isRecommended && (
        <View style={{ position: 'absolute', top: -10, left: 12,
          backgroundColor: '#10B981', borderRadius: 999, paddingHorizontal: 10, paddingVertical: 3, zIndex: 1 }}>
          <Text style={{ color: 'white', fontSize: 10, fontWeight: '800', letterSpacing: 0.2 }}>
            내 조건 {item.matchPct}% 일치
          </Text>
        </View>
      )}
      <View style={{ flexDirection: 'row', gap: 12, padding: 12 }}>
        {/* 썸네일 */}
        <View style={{ width: 96, height: 96, borderRadius: 10, backgroundColor: '#E4E4E7',
          flexShrink: 0, overflow: 'hidden', position: 'relative' }}>
          <Image source={listingThumb(item.id)} style={{ width: 96, height: 96 }} resizeMode="cover" />
          {item.isNew && (
            <View style={{ position: 'absolute', top: 6, left: 6,
              backgroundColor: '#10B981', borderRadius: 3, paddingHorizontal: 5, paddingVertical: 2 }}>
              <Text style={{ color: 'white', fontSize: 9, fontWeight: '800', letterSpacing: 0.4 }}>NEW</Text>
            </View>
          )}
          <View style={{ position: 'absolute', bottom: 6, right: 6,
            backgroundColor: 'rgba(10,10,11,0.7)', borderRadius: 4, paddingHorizontal: 5, paddingVertical: 2 }}>
            <Text style={{ color: 'white', fontSize: 10, fontWeight: '600' }}>+{item.photoCount}</Text>
          </View>
        </View>

        {/* 정보 */}
        <View style={{ flex: 1, gap: 3 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: 6, flex: 1, marginRight: 8 }}>
              {item.name && (
                <Text style={{ fontSize: 14, fontWeight: '800', color: '#0A0A0B', letterSpacing: -0.2, flexShrink: 1 }} numberOfLines={1}>
                  {item.name}
                </Text>
              )}
              <Text style={{ fontSize: 11, fontWeight: '700', color: '#71717A', letterSpacing: 0.4 }}>
                {item.kind}
              </Text>
            </View>
            <Pressable onPress={() => onToggleSave(item.id)}
              style={{ width: 28, height: 28, alignItems: 'center', justifyContent: 'center', marginTop: -4, marginRight: -4 }}>
              <Ionicons name={item.isSaved ? 'heart' : 'heart-outline'} size={18}
                color={item.isSaved ? '#EF4444' : '#A1A1AA'} />
            </Pressable>
          </View>
          <Text style={{ fontSize: 17, fontWeight: '800', letterSpacing: -0.34, color: '#0A0A0B', lineHeight: 22 }}>
            <Text>보증 {item.deposit}</Text>
            <Text style={{ fontSize: 14, fontWeight: '700', color: '#3F3F46' }}> / 월 {item.monthly}</Text>
          </Text>
          <Text style={{ fontSize: 12, color: '#71717A' }}>
            {item.area} · {item.floor}
          </Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 5, marginTop: 2 }}>
            {item.badges.map(({ variant, label }) => {
              const s = BADGE_STYLE[variant];
              const hasDot = variant === 'safe' || variant === 'mid' || variant === 'danger';
              return (
                <View key={label} style={{ flexDirection: 'row', alignItems: 'center', gap: 3,
                  backgroundColor: s.bg, borderRadius: 999, paddingHorizontal: 8, paddingVertical: 3 }}>
                  {hasDot && <View style={{ width: 5, height: 5, borderRadius: 3, backgroundColor: s.text }} />}
                  <Text style={{ fontSize: 11, fontWeight: '700', color: s.text }}>{label}</Text>
                </View>
              );
            })}
          </View>
        </View>
      </View>
    </Pressable>
  );
}

/* ─── EmptyState ─── */
function EmptyState() {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40, gap: 12 }}>
      <View style={{ width: 80, height: 80, borderRadius: 40, backgroundColor: '#F4F4F5',
        alignItems: 'center', justifyContent: 'center', marginBottom: 8 }}>
        <Ionicons name="search-outline" size={32} color="#A1A1AA" />
      </View>
      <Text style={{ fontSize: 17, fontWeight: '800', color: '#0A0A0B', textAlign: 'center' }}>
        조건에 맞는 매물이 없어요
      </Text>
      <Text style={{ fontSize: 13, color: '#71717A', textAlign: 'center', lineHeight: 20 }}>
        {'내 조건이 너무 좁아요.\n아래 옵션 중 하나를 시도해보세요.'}
      </Text>
      <View style={{ width: '100%', marginTop: 16, gap: 8 }}>
        {([
          { label: '위험도 "주의"까지 보기 (8건 추가)', primary: true },
          { label: '예산을 보증 4,000만까지 (5건 추가)', primary: false },
          { label: '다른 동네 보기 (왕십리·뚝섬)', primary: false },
        ]).map(({ label, primary }) => (
          <Pressable key={label}
            style={{ paddingVertical: 12, borderRadius: 10, alignItems: 'center', justifyContent: 'center',
              backgroundColor: primary ? '#10B981' : 'white',
              borderWidth: primary ? 0 : 1, borderColor: '#E4E4E7' }}>
            <Text style={{ fontSize: 14, fontWeight: '700', color: primary ? 'white' : '#3F3F46' }}>{label}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

/* ─── Main Screen ─── */
type SortKey = 'price' | 'area' | 'year';
const SORT_CHIPS: { key: SortKey; label: string }[] = [
  { key: 'price', label: '가격' },
  { key: 'area', label: '면적' },
  { key: 'year', label: '연식' },
];

export default function SearchScreen() {
  const results = useDiagnosisStore((s) => s.results);
  const setResults = useDiagnosisStore((s) => s.setResults);
  const { areaId } = useLocalSearchParams<{ areaId?: string }>();

  // 새로고침/재진입 = store 휘발 → 세션 최근 추천 복원
  useEffect(() => {
    if (results.length === 0) {
      getLatestRecommend()
        .then((res) => {
          if (res.areas?.length) setResults(res.areas, res.match_id);
          // 라이프스타일 태그도 복원 — 입지 미니 타일 개인화용
          const names = (res.request as { lifestyle_tags?: string[] } | undefined)?.lifestyle_tags;
          if (names && names.length > 0) {
            useDiagnosisStore.setState({
              lifestyleTags: names.map((n) => ({ id: n, name: n })),
            });
          }
        })
        .catch((e) => console.log('[search] restore error', e?.response?.status));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const area = useMemo(
    () => results.find((a) => a.area_id === areaId) ?? results[0],
    [results, areaId]
  );

  const [sort, setSort] = useState<{ key: SortKey; dir: 'asc' | 'desc' }>({ key: 'price', dir: 'asc' });
  const favIds = useFavoriteStore((s) => s.ids);
  const toggleSave = useFavoriteStore((s) => s.toggle);

  const listings = useMemo(() => {
    const arr = [...(area?.listings ?? [])];
    const val = (l: RecListing) =>
      sort.key === 'price'
        ? l.deposit + l.monthly_rent * 12
        : sort.key === 'area'
          ? (l.area_m2 ?? 0)
          : (l.build_year ?? 0);
    arr.sort((a, b) => (sort.dir === 'asc' ? val(a) - val(b) : val(b) - val(a)));
    return arr.map((l, i) => ({ ...toCard(l, area, i), isSaved: favIds.has(l.id) }));
  }, [area, sort, favIds]);
  const isEmpty = listings.length === 0;

  const pickSort = (key: SortKey) =>
    setSort((s) =>
      s.key === key
        ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: key === 'year' ? 'desc' : 'asc' }, // 연식은 신축순(desc) 기본
    );

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
      {/* 앱 바 */}
      <View style={{ height: 56, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', gap: 8,
        borderBottomWidth: 1, borderBottomColor: '#F4F4F5' }}>
        <Pressable onPress={() => router.push('/diagnosis/complete')}
          style={{ width: 40, height: 40, alignItems: 'center', justifyContent: 'center', borderRadius: 999 }}>
          <Ionicons name="chevron-back" size={22} color="#0A0A0B" />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={{ fontSize: 16, fontWeight: '700', letterSpacing: -0.16, color: '#0A0A0B' }}>
            {area?.name ?? '동네'}
          </Text>
          <Text style={{ fontSize: 11, color: '#71717A', marginTop: 1 }}>
            {area ? `매칭점수 ${area.score} · 통근 약 ${area.commuteMinutes}분` : '진단 결과를 먼저 확인해주세요'}
          </Text>
        </View>
        <View style={{ width: 40, height: 40 }} />
      </View>

      {/* 정렬 칩바 — 가격/면적/연식, 탭하면 오름↔내림 토글 */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        bounces={false}
        alwaysBounceHorizontal={false}
        style={{ flexGrow: 0, flexShrink: 0, borderBottomWidth: 1, borderBottomColor: '#F4F4F5' }}
        contentContainerStyle={{
          paddingHorizontal: 16,
          paddingVertical: 10,
          gap: 8,
          flexDirection: 'row',
          alignItems: 'center',
          paddingRight: 24,
        }}>
        {SORT_CHIPS.map(({ key, label }) => {
          const isActive = sort.key === key;
          return (
            <Pressable key={key} onPress={() => pickSort(key)}
              style={{ flexShrink: 0, paddingHorizontal: 14, paddingVertical: 9, borderRadius: 999,
                flexDirection: 'row', alignItems: 'center', gap: 5, borderWidth: 1,
                borderColor: isActive ? '#0A0A0B' : '#E4E4E7',
                backgroundColor: isActive ? '#0A0A0B' : 'white' }}>
              <Text style={{ fontSize: 13, fontWeight: '600', color: isActive ? 'white' : '#3F3F46' }}>{label}</Text>
              {isActive && (
                <Ionicons
                  name={
                    key === 'year'
                      ? sort.dir === 'desc' ? 'arrow-down' : 'arrow-up' // 신축(desc)=↓
                      : sort.dir === 'asc' ? 'arrow-down' : 'arrow-up'
                  }
                  size={12}
                  color="white"
                />
              )}
            </Pressable>
          );
        })}
      </ScrollView>

      {/* 결과 수 바 */}
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
        paddingHorizontal: 16, paddingTop: 12, paddingBottom: 4 }}>
        {isEmpty ? (
          <Text style={{ fontSize: 13, color: '#3F3F46' }}><Text style={{ fontWeight: '700', color: '#0A0A0B' }}>0</Text>건</Text>
        ) : (
          <Text style={{ fontSize: 13, color: '#3F3F46' }}>
            <Text style={{ fontWeight: '700', color: '#0A0A0B' }}>{listings.length}</Text>건 ·{' '}
            <Text style={{ fontWeight: '700', color: '#059669' }}>
              안전 매물 {listings.filter((l) => l.badges.some((b) => b.variant === 'safe')).length}건
            </Text>
          </Text>
        )}
        <View style={{ flexDirection: 'row', borderWidth: 1, borderColor: '#E4E4E7', borderRadius: 6, overflow: 'hidden' }}>
          {(['list', 'grid'] as const).map((v, i) => (
            <Pressable key={v} style={{ width: 32, height: 28, alignItems: 'center', justifyContent: 'center',
              backgroundColor: i === 0 ? '#0A0A0B' : 'white' }}>
              <Ionicons name={v === 'list' ? 'list-outline' : 'grid-outline'} size={13}
                color={i === 0 ? 'white' : '#71717A'} />
            </Pressable>
          ))}
        </View>
      </View>

      {/* 리스트 / 빈 상태 */}
      {isEmpty ? (
        <EmptyState />
      ) : (
        <FlatList
          data={listings}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <ListingCard item={item} onToggleSave={toggleSave} />}
          contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 16, paddingBottom: 20, gap: 12 }}
          showsVerticalScrollIndicator={false}
        />
      )}

      <TabBar />
    </SafeAreaView>
  );
}