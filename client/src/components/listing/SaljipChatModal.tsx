// 살집이 챗 모달 — 자율형 챗봇 UI 흉내, 안에 3 카드 그리드.
// 카드 탭 시 sheet 띄움. 챗 입력은 placeholder만 (BETA).
import { useEffect, useState } from 'react';
import { View, Text, Pressable, ScrollView, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ContractSheet } from './sheets/ContractSheet';
import { NegotiationSheet } from './sheets/NegotiationSheet';
import { LandlordSheet } from './sheets/LandlordSheet';

type SheetKey = 'contract' | 'negotiation' | 'landlord' | null;

const NEUTRAL = {
  ink: '#0A0A0B',
  ink2: '#18181B',
  text: '#27272A',
  textMute: '#71717A',
  border: '#E4E4E7',
  borderFaint: '#F4F4F5',
  surface: '#FAFAFA',
};

interface CardDef {
  key: Exclude<SheetKey, null>;
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  sub: string;
}

const CARDS: CardDef[] = [
  { key: 'contract',    icon: 'document-text-outline',     title: '계약서 위험 분석', sub: '독소·사기 조항 탐지' },
  { key: 'negotiation', icon: 'chatbubble-ellipses-outline', title: '협상 멘트 생성',  sub: '시세 근거 협상 문구' },
  { key: 'landlord',    icon: 'person-circle-outline',     title: '임대인 신뢰도',    sub: 'HUG·등기·체납 검증' },
];

export interface SaljipChatModalProps {
  visible: boolean;
  onClose: () => void;
  listingTitle: string;
  ownerLabel: string;
}

export function SaljipChatModal({
  visible, onClose, listingTitle, ownerLabel,
}: SaljipChatModalProps) {
  const [open, setOpen] = useState<SheetKey>(null);

  if (!visible) return null;
  return (
    <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 25 }}>
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
        <View style={{
          flexDirection: 'row', alignItems: 'center', gap: 10,
          paddingHorizontal: 16, paddingVertical: 12,
          borderBottomWidth: 1, borderBottomColor: NEUTRAL.borderFaint,
        }}>
          <View style={{
            width: 36, height: 36, borderRadius: 18, backgroundColor: '#0A0A0B',
            alignItems: 'center', justifyContent: 'center',
          }}>
            <Ionicons name="chatbubbles" size={18} color="white" />
          </View>
          <View style={{ flex: 1 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
              <Text style={{ fontSize: 16, fontWeight: '800', color: NEUTRAL.ink }}>살집이</Text>
              <View style={{
                flexDirection: 'row', alignItems: 'center', gap: 3,
                backgroundColor: '#FEF3C7', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4,
              }}>
                <Ionicons name="alert-circle" size={10} color="#B45309" />
                <Text style={{ fontSize: 10, fontWeight: '700', color: '#B45309' }}>추후 구현 예정</Text>
              </View>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 2 }}>
              <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: '#10B981' }} />
              <Text style={{ fontSize: 11, color: NEUTRAL.textMute }}>온라인 · AI 매물 분석가</Text>
            </View>
          </View>
          <Pressable onPress={onClose}
            style={{ width: 32, height: 32, alignItems: 'center', justifyContent: 'center' }}>
            <Ionicons name="close" size={22} color={NEUTRAL.ink} />
          </Pressable>
        </View>

        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 32 }}>
          {/* 챗 인사말 */}
          <ChatBubble delay={120}>
            안녕하세요, 살집이에요. 👋{'\n'}
            <Text style={{ fontWeight: '800' }}>{listingTitle}</Text>에 대해 무엇을 도와드릴까요?
          </ChatBubble>

          {/* 3 카드 그리드 — 빠른 액션 */}
          <View style={{ marginTop: 12 }}>
            <Text style={{ fontSize: 10, fontWeight: '800', color: NEUTRAL.textMute, letterSpacing: 0.5, marginBottom: 8, paddingLeft: 4 }}>
              빠른 분석
            </Text>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              {CARDS.map((c, i) => (
                <CardButton key={c.key} card={c} delay={600 + i * 140} onPress={() => setOpen(c.key)} />
              ))}
            </View>
          </View>
        </ScrollView>

        {/* 비활성 챗 입력바 — UI만 */}
        <View style={{
          flexDirection: 'row', alignItems: 'center', gap: 8,
          paddingHorizontal: 12, paddingVertical: 10,
          borderTopWidth: 1, borderTopColor: NEUTRAL.borderFaint,
          backgroundColor: 'white',
        }}>
          <View style={{
            flex: 1, backgroundColor: NEUTRAL.surface,
            borderRadius: 20, paddingHorizontal: 14, paddingVertical: 10,
            opacity: 0.7,
          }}>
            <Text style={{ fontSize: 13, color: NEUTRAL.textMute }}>
              자유 대화는 곧 제공됩니다
            </Text>
          </View>
          <View style={{
            width: 36, height: 36, borderRadius: 18, backgroundColor: '#E4E4E7',
            alignItems: 'center', justifyContent: 'center',
          }}>
            <Ionicons name="send" size={14} color="#A1A1AA" />
          </View>
        </View>
      </View>

      {/* 하위 시트들 */}
      <ContractSheet
        visible={open === 'contract'}
        onClose={() => setOpen(null)}
      />
      <NegotiationSheet
        visible={open === 'negotiation'}
        onClose={() => setOpen(null)}
        listingTitle={listingTitle}
      />
      <LandlordSheet
        visible={open === 'landlord'}
        onClose={() => setOpen(null)}
        ownerLabel={ownerLabel}
      />
    </View>
  );
}

function ChatBubble({ children, delay }: { children: React.ReactNode; delay: number }) {
  const [opacity] = useState(new Animated.Value(0));
  const [translate] = useState(new Animated.Value(6));
  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, { toValue: 1, duration: 220, delay, useNativeDriver: true }),
      Animated.timing(translate, { toValue: 0, duration: 220, delay, useNativeDriver: true }),
    ]).start();
  }, [opacity, translate, delay]);
  return (
    <Animated.View style={{
      opacity, transform: [{ translateY: translate }],
      flexDirection: 'row', gap: 8, marginBottom: 8,
    }}>
      <View style={{
        width: 24, height: 24, borderRadius: 12, backgroundColor: '#0A0A0B',
        alignItems: 'center', justifyContent: 'center', marginTop: 2,
      }}>
        <Ionicons name="chatbubble-ellipses" size={11} color="white" />
      </View>
      <View style={{
        flex: 1, backgroundColor: 'white',
        borderRadius: 14, borderTopLeftRadius: 4,
        paddingHorizontal: 12, paddingVertical: 10,
        borderWidth: 1, borderColor: NEUTRAL.borderFaint,
      }}>
        <Text style={{ fontSize: 13, color: NEUTRAL.text, lineHeight: 20 }}>{children}</Text>
      </View>
    </Animated.View>
  );
}

function CardButton({ card, delay, onPress }: { card: CardDef; delay: number; onPress: () => void }) {
  const [opacity] = useState(new Animated.Value(0));
  const [translate] = useState(new Animated.Value(6));
  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, { toValue: 1, duration: 220, delay, useNativeDriver: true }),
      Animated.timing(translate, { toValue: 0, duration: 220, delay, useNativeDriver: true }),
    ]).start();
  }, [opacity, translate, delay]);
  return (
    <Animated.View style={{ flex: 1, opacity, transform: [{ translateY: translate }] }}>
      <Pressable
        onPress={onPress}
        style={({ pressed }) => ({
          opacity: pressed ? 0.7 : 1,
          backgroundColor: 'white',
          borderWidth: 1, borderColor: NEUTRAL.borderFaint,
          borderRadius: 12, padding: 12, gap: 6,
          minHeight: 108,
        })}>
        <View style={{ width: 32, height: 32, borderRadius: 8, backgroundColor: '#F4F4F5',
          alignItems: 'center', justifyContent: 'center' }}>
          <Ionicons name={card.icon} size={16} color={NEUTRAL.ink2} />
        </View>
        <Text style={{ fontSize: 11, fontWeight: '800', color: NEUTRAL.ink, lineHeight: 14 }}>
          {card.title}
        </Text>
        <Text style={{ fontSize: 9, color: NEUTRAL.textMute, lineHeight: 13 }}>
          {card.sub}
        </Text>
      </Pressable>
    </Animated.View>
  );
}
