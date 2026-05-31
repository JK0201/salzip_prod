// 공통 BottomSheet 셸 — 헤더 + 상태 라벨 + 닫기 버튼.
import { View, Text, Pressable, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ReactNode } from 'react';

const NEUTRAL = {
  ink: '#0A0A0B',
  ink2: '#18181B',
  text: '#27272A',
  textMute: '#71717A',
  surface: '#FAFAFA',
  iconBg: '#F4F4F5',
  border: '#E4E4E7',
};

export interface SheetShellProps {
  visible: boolean;
  onClose: () => void;
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  sub: string;
  /** 우상단 상태 ("생성 중" / "완료" 등) */
  statusLabel?: string;
  statusColor?: string;
  children: ReactNode;
}

export function SheetShell({
  visible, onClose, icon, title, sub,
  statusLabel, statusColor, children,
}: SheetShellProps) {
  if (!visible) return null;
  return (
    <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 30 }}>
      <Pressable style={{ flex: 1, backgroundColor: 'rgba(10,10,11,0.5)' }} onPress={onClose} />
      <View style={{
        position: 'absolute', top: 60, left: 0, right: 0, bottom: 0,
        backgroundColor: NEUTRAL.surface,
        borderTopLeftRadius: 20, borderTopRightRadius: 20,
      }}>
        {/* 핸들 */}
        <View style={{ alignItems: 'center', paddingTop: 8, paddingBottom: 4 }}>
          <View style={{ width: 36, height: 4, borderRadius: 2, backgroundColor: '#D4D4D8' }} />
        </View>
        {/* 헤더 */}
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 16, paddingVertical: 12 }}>
          <View style={{ width: 40, height: 40, borderRadius: 10, backgroundColor: NEUTRAL.iconBg,
            alignItems: 'center', justifyContent: 'center' }}>
            <Ionicons name={icon} size={20} color={NEUTRAL.ink2} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: NEUTRAL.ink }}>{title}</Text>
            <Text style={{ fontSize: 11, color: NEUTRAL.textMute, marginTop: 2 }}>{sub}</Text>
          </View>
          {statusLabel && (
            <Text style={{ fontSize: 11, fontWeight: '700', color: statusColor ?? NEUTRAL.ink }}>
              {statusLabel}
            </Text>
          )}
          <Pressable onPress={onClose}
            style={{ width: 32, height: 32, alignItems: 'center', justifyContent: 'center', marginLeft: 4 }}>
            <Ionicons name="close" size={22} color={NEUTRAL.ink} />
          </Pressable>
        </View>

        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 32 }}>
          {children}
        </ScrollView>
      </View>
    </View>
  );
}
