import { Ionicons } from '@expo/vector-icons';
import { router, usePathname } from 'expo-router';
import { Pressable, Text, View } from 'react-native';

const TABS = [
  { label: '지도',    icon: 'map-outline',              route: '/(onboarding)/diagnosis/complete' },
  { label: '검색',    icon: 'search-outline',           route: '/search' },
  { label: '지원사업', icon: 'checkmark-circle-outline', route: '/(main)/hsubsidy' },
  { label: '마이',    icon: 'person-outline',           route: '/(main)/mypage' },
] as const;

interface Props {
  activeTab?: '지도' | '검색' | '지원사업' | '마이';
}

export function TabBar({ activeTab }: Props) {
  const path = usePathname();

  const resolveActive = (): string => {
    if (activeTab) return activeTab;
    if (path.includes('mypage')) return '마이';
    if (path.includes('search')) return '검색';
    if (path.includes('hsubsidy')) return '지원사업';
    if (path.includes('complete')) return '지도';
    return '지도';
  };

  const active = resolveActive();

  return (
    <View className="flex-row border-t border-[#F4F4F5] bg-white pb-1" style={{ height: 52 }}>
      {TABS.map(({ label, icon, route }) => {
        const isActive = active === label;
        return (
          <Pressable
            key={label}
            className="flex-1 items-center justify-center gap-0.5 active:opacity-70"
            onPress={() => route && router.navigate(route as never)}
          >
            <Ionicons name={icon as never} size={18} color={isActive ? '#0A0A0B' : '#A1A1AA'} />
            <Text style={{ fontSize: 9, fontWeight: isActive ? '700' : '500', color: isActive ? '#0A0A0B' : '#A1A1AA' }}>
              {label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}
