import { useEffect, useState } from 'react';
import { View, Text, ScrollView, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { ProfileHero } from '@/components/profile/ProfileHero';
import { DiagnoseCard } from '@/components/profile/DiagnoseCard';
import { ActiveApplicationCard } from '@/components/profile/ActiveApplicationCard';
import { SavedTabs, type SavedTabKey } from '@/components/profile/SavedTabs';
import { SavedListingItem } from '@/components/profile/SavedListingItem';
import { SectionHeader, MenuItem } from '@/components/profile/MenuItem';
import { TabBar } from '@/components/TabBar';
import { logout, createSession } from '@/api/session';
import { getFavorites, type FavoriteItem } from '@/api/favorites';
import { getLatestRecommend } from '@/api/recommend';
import { useSessionStore, SESSION_KEY, SESSION_EXPIRES_KEY, USER_NAME_KEY } from '@/store/useSessionStore';
import { useFavoriteStore } from '@/store/useFavoriteStore';

import {
  MOCK_PROFILE,
  MOCK_STATS,
  MOCK_DIAGNOSE,
  MOCK_ACTIVE_APPLICATION,
} from '@/constants/mypageMock';

export function MyPageScreen() {
  const [savedTab, setSavedTab] = useState<SavedTabKey>('listing');
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [showAllSaved, setShowAllSaved] = useState(false);
  const [daysAgo, setDaysAgo] = useState<number>(MOCK_DIAGNOSE.lastDiagnoseDaysAgo);
  const [diagInfo, setDiagInfo] = useState<{ age?: number; job?: string }>({});
  const favIds = useFavoriteStore((s) => s.ids);
  const toggleFav = useFavoriteStore((s) => s.toggle);
  const userName = useSessionStore((s) => s.userName);

  const profile = {
    ...MOCK_PROFILE,
    name: userName ?? MOCK_PROFILE.name,
    age: diagInfo.age ?? MOCK_PROFILE.age,
    job: diagInfo.job ?? MOCK_PROFILE.job,
  };
  const stats = { ...MOCK_STATS, savedListings: favorites.length, savedNeighborhoods: 0 };

  // 찜 목록은 진입 시 1회만 로드. 하트 해제해도 카드는 유지(색만 빠짐), 다음 진입 때 사라짐.
  useEffect(() => {
    getFavorites()
      .then((res) => setFavorites(res.items))
      .catch((e) => console.log('[mypage] favorites 로드 실패', e?.response?.status));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 마지막 진단 경과일 (latest.created_at 기준)
  useEffect(() => {
    getLatestRecommend()
      .then((res) => {
        if (res.created_at) {
          const ms = Date.now() - new Date(res.created_at).getTime();
          setDaysAgo(Math.max(0, Math.floor(ms / 86400000)));
        }
        if (res.request) {
          setDiagInfo({ age: res.request.age, job: res.request.job_type });
        }
      })
      .catch(() => {});
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // 서버 로그아웃 실패해도 로컬 세션 제거
    }
    await AsyncStorage.removeItem(SESSION_KEY);
    await AsyncStorage.removeItem(SESSION_EXPIRES_KEY);
    await AsyncStorage.removeItem(USER_NAME_KEY);
    useSessionStore.getState().clearSession();
    useFavoriteStore.getState().clear();

    // 로그아웃 후 익명 세션 즉시 재발급 (없으면 이후 요청 401)
    try {
      const s = await createSession();
      await AsyncStorage.setItem(SESSION_KEY, s.token);
      await AsyncStorage.setItem(SESSION_EXPIRES_KEY, s.expires_at);
      useSessionStore.getState().setSession(s.token, s.expires_at);
    } catch {
      // 실패해도 인터셉터가 다음 401에서 재발급
    }

    router.replace('/(onboarding)/start' as never);
  };

  const noop = () => {
    // TODO: 라우팅 연결
  };

  return (
    <SafeAreaView className="flex-1 bg-neutral-50">
      {/* AppBar */}
      <View className="flex-row items-center justify-between px-6 pb-3 pt-4">
        <Text className="text-2xl font-extrabold text-neutral-900">마이</Text>
        <Pressable onPress={noop} className="h-9 w-9 items-center justify-center">
          <Ionicons name="settings-outline" size={22} color="#0A0A0B" />
        </Pressable>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerClassName="pb-6"
      >
        {/* 1. 프로필 히어로 */}
        <ProfileHero profile={profile} stats={stats} onPressEdit={noop} />

        {/* 2. 재진단 카드 */}
        <DiagnoseCard
          daysAgo={daysAgo}
          onPress={() => router.replace('/(onboarding)/start' as never)}
        />

        {/* 3. 진행 중 신청 */}
        <View className="mt-6 px-6">
          <SectionHeader title="진행 중 신청" action="전체 보기" onPressAction={noop} />
        </View>
        <View className="mx-5">
          <ActiveApplicationCard application={MOCK_ACTIVE_APPLICATION} />
        </View>

        {/* 4. 저장한 항목 */}
        <View className="mt-6 px-6">
          <SectionHeader title="저장한 항목" action="정렬 · 관리" onPressAction={noop} />
          <SavedTabs
            active={savedTab}
            listingCount={favorites.length}
            neighborhoodCount={0}
            onChange={setSavedTab}
          />
        </View>
        <View className="mx-5 gap-2.5">
          {savedTab === 'listing' &&
            (favorites.length === 0 ? (
              <View className="items-center rounded-xl bg-white py-10">
                <Text className="text-sm text-neutral-400">저장한 매물이 없어요</Text>
              </View>
            ) : (
              <>
                {(showAllSaved ? favorites : favorites.slice(0, 3)).map((listing) => (
                  <SavedListingItem
                    key={listing.listing_id}
                    listing={listing}
                    isSaved={favIds.has(listing.listing_id)}
                    onPress={() => router.push(`/listing/${listing.listing_id}` as never)}
                    onToggleSave={() => toggleFav(listing.listing_id)}
                  />
                ))}
                {favorites.length > 3 && (
                  <Pressable
                    onPress={() => setShowAllSaved((v) => !v)}
                    className="items-center rounded-xl border border-neutral-200 bg-white py-3"
                  >
                    <Text className="text-sm font-semibold text-neutral-500">
                      {showAllSaved ? '접기' : `더보기 (${favorites.length - 3})`}
                    </Text>
                  </Pressable>
                )}
              </>
            ))}
          {savedTab === 'neighborhood' && (
            <View className="items-center rounded-xl bg-white py-10">
              <Text className="text-sm text-neutral-400">저장한 동네가 없어요</Text>
            </View>
          )}
        </View>

        {/* 5. 설정 메뉴 */}
        <View className="mt-6 px-6">
          <SectionHeader title="설정" />
        </View>
        <View className="mx-5 overflow-hidden rounded-2xl border border-neutral-200 bg-white">
          <MenuItem
            iconName="notifications-outline"
            title="알림 설정"
            desc="신청 단계 알림 · 마감 임박 · 마케팅"
            onPress={noop}
          />
          <MenuItem
            iconName="moon-outline"
            title="화면 모드"
            desc="시스템 기본"
            onPress={noop}
          />
          <MenuItem
            iconName="lock-closed-outline"
            title="계정 · 보안"
            desc="이메일·비밀번호·로그인 기기"
            onPress={noop}
          />
          <MenuItem
            iconName="document-text-outline"
            title="내 데이터 관리"
            desc="진단 내역·저장 항목 다운로드 / 삭제"
            onPress={noop}
          />
          <MenuItem
            iconName="help-circle-outline"
            title="고객센터 · 도움말"
            desc="자주 묻는 질문 · 문의하기"
            onPress={noop}
          />
          <MenuItem
            iconName="information-circle-outline"
            title="약관 · 정책"
            desc="이용약관 · 개인정보처리방침"
            onPress={noop}
            isLast
          />
        </View>

        {/* 로그아웃 */}
        <Pressable
          onPress={handleLogout}
          className="mx-5 mt-4 items-center rounded-xl bg-neutral-100 py-3.5"
        >
          <Text className="text-sm font-semibold text-neutral-500">로그아웃</Text>
        </Pressable>

        {/* 푸터 */}
        <View className="items-center px-6 py-6">
          <Text className="text-[11px] text-neutral-400">Salzip v0.1.0</Text>
          <Text className="mt-1 text-[11px] text-neutral-400">
            © 2026 Salzip Team
          </Text>
        </View>
      </ScrollView>

      <TabBar />
    </SafeAreaView>
  );
}
