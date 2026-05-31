// 분석 리포트 메일 발송 시트 (BETA mock).
// 이메일 입력 → "발송 예약됨" 토스트. 실제 발송 없음.
import { useState } from 'react';
import { View, Text, TextInput, Pressable, Alert } from 'react-native';
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

const REPORT_INCLUDES = [
  { icon: 'shield-checkmark-outline', label: '깡통전세 위험도 4축 분석' },
  { icon: 'pricetag-outline',         label: '주변 실거래가 비교' },
  { icon: 'location-outline',         label: '동네 인프라 8종 평가' },
  { icon: 'cash-outline',             label: '청년 지원사업 매칭 결과' },
  { icon: 'document-text-outline',    label: 'AI 종합 의견' },
] as const;

export interface EmailSheetProps {
  visible: boolean;
  onClose: () => void;
  listingTitle: string;
}

export function EmailSheet({ visible, onClose, listingTitle }: EmailSheetProps) {
  const [email, setEmail] = useState('');
  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());

  const onSubmit = () => {
    if (!valid) return;
    Alert.alert(
      '발송 예약 완료',
      `${email.trim()} 으로 분석 리포트를 보내드립니다.`,
      [{ text: '확인', onPress: onClose }],
    );
  };

  return (
    <SheetShell
      visible={visible}
      onClose={onClose}
      icon="mail-outline"
      title="분석 리포트 메일 받기"
      sub="PDF로 정리된 분석 결과 발송"
    >
      {/* 리포트 미리보기 — 무엇이 들어있는지 */}
      <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14, marginBottom: 12 }}>
        <Text style={{ fontSize: 10, fontWeight: '800', color: NEUTRAL.textMute, letterSpacing: 0.5, marginBottom: 10 }}>
          리포트 구성
        </Text>
        <View style={{ borderRadius: 8, borderWidth: 1, borderColor: NEUTRAL.borderFaint, padding: 10, marginBottom: 10 }}>
          <Text style={{ fontSize: 12, fontWeight: '700', color: NEUTRAL.ink }} numberOfLines={1}>
            {listingTitle}
          </Text>
          <Text style={{ fontSize: 10, color: NEUTRAL.textMute, marginTop: 2 }}>
            SALZIP 매물 진단 리포트 · A4 5p (예상)
          </Text>
        </View>
        <View style={{ gap: 8 }}>
          {REPORT_INCLUDES.map((r) => (
            <View key={r.label} style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Ionicons name={r.icon as keyof typeof Ionicons.glyphMap} size={14} color={NEUTRAL.ink2} />
              <Text style={{ fontSize: 12, color: NEUTRAL.text }}>{r.label}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* 이메일 입력 */}
      <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14, marginBottom: 12 }}>
        <Text style={{ fontSize: 10, fontWeight: '800', color: NEUTRAL.textMute, letterSpacing: 0.5, marginBottom: 8 }}>
          받을 이메일 주소
        </Text>
        <TextInput
          value={email}
          onChangeText={setEmail}
          placeholder="you@example.com"
          placeholderTextColor="#A1A1AA"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="email-address"
          style={{
            borderWidth: 1, borderColor: valid ? '#10B981' : NEUTRAL.border,
            borderRadius: 8, paddingHorizontal: 12, paddingVertical: 10,
            fontSize: 14, color: NEUTRAL.ink,
          }}
        />
        <Text style={{ fontSize: 10, color: NEUTRAL.textMute, marginTop: 6 }}>
          입력하신 주소로만 발송되며, 마케팅 목적으로 사용되지 않습니다.
        </Text>
      </View>

      {/* CTA */}
      <Pressable
        onPress={onSubmit}
        disabled={!valid}
        style={{
          backgroundColor: valid ? '#0A0A0B' : '#D4D4D8',
          borderRadius: 12, paddingVertical: 14,
          flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
        }}>
        <Ionicons name="paper-plane-outline" size={16} color="white" />
        <Text style={{ color: 'white', fontSize: 14, fontWeight: '800' }}>
          리포트 발송 예약하기
        </Text>
      </Pressable>
    </SheetShell>
  );
}
