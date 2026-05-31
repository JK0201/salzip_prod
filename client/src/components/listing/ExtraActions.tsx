// listing 상세 inline — 2 카드 (BETA 미리보기, LLM 무관 유틸).
// 출퇴근 노선 상세 / 분석 리포트 메일 받기.
import { useState } from 'react';
import { View, Text, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { RouteSheet } from './sheets/RouteSheet';
import { EmailSheet } from './sheets/EmailSheet';

type SheetKey = 'route' | 'email' | null;

const NEUTRAL = {
  ink: '#0A0A0B',
  ink2: '#18181B',
  text: '#27272A',
  textMute: '#71717A',
  borderFaint: '#F4F4F5',
};

interface CardDef {
  key: Exclude<SheetKey, null>;
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  sub: string;
}

const CARDS: CardDef[] = [
  { key: 'route', icon: 'bus-outline',  title: '출퇴근 노선 상세', sub: '대중교통 다중 경로' },
  { key: 'email', icon: 'mail-outline', title: '메일로 리포트',    sub: '분석 결과 PDF 발송' },
];

export interface ExtraActionsProps {
  originArea: string;
  destLabel: string;
  listingTitle: string;
}

export function ExtraActions({ originArea, destLabel, listingTitle }: ExtraActionsProps) {
  const [open, setOpen] = useState<SheetKey>(null);

  return (
    <>
      <View style={{ paddingHorizontal: 16, paddingTop: 18 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 10 }}>
          <Ionicons name="apps-outline" size={13} color={NEUTRAL.ink2} />
          <Text style={{ fontSize: 11, fontWeight: '800', color: NEUTRAL.ink, letterSpacing: 0.4 }}>
            부가 기능
          </Text>
          <View style={{
            flexDirection: 'row', alignItems: 'center', gap: 3,
            backgroundColor: '#FEF3C7', paddingHorizontal: 5, paddingVertical: 1, borderRadius: 3,
          }}>
            <Ionicons name="alert-circle" size={9} color="#B45309" />
            <Text style={{ fontSize: 9, fontWeight: '700', color: '#B45309' }}>
              추후 구현 예정
            </Text>
          </View>
        </View>

        <View style={{ flexDirection: 'row', gap: 8 }}>
          {CARDS.map((c) => (
            <Pressable
              key={c.key}
              onPress={() => setOpen(c.key)}
              style={({ pressed }) => ({
                flex: 1, opacity: pressed ? 0.7 : 1,
                backgroundColor: 'white',
                borderWidth: 1, borderColor: NEUTRAL.borderFaint,
                borderRadius: 12, padding: 12,
                flexDirection: 'row', alignItems: 'center', gap: 10,
              })}>
              <View style={{ width: 36, height: 36, borderRadius: 8, backgroundColor: '#F4F4F5',
                alignItems: 'center', justifyContent: 'center' }}>
                <Ionicons name={c.icon} size={18} color={NEUTRAL.ink2} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 12, fontWeight: '800', color: NEUTRAL.ink, lineHeight: 15 }}>
                  {c.title}
                </Text>
                <Text style={{ fontSize: 10, color: NEUTRAL.textMute, marginTop: 2 }}>
                  {c.sub}
                </Text>
              </View>
            </Pressable>
          ))}
        </View>
      </View>

      <RouteSheet
        visible={open === 'route'}
        onClose={() => setOpen(null)}
        originArea={originArea}
        destLabel={destLabel}
      />
      <EmailSheet
        visible={open === 'email'}
        onClose={() => setOpen(null)}
        listingTitle={listingTitle}
      />
    </>
  );
}
