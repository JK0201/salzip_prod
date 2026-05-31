// Route: /(main)/hsubsidy (S07 지원사업 진단)
import { useState } from 'react';
import type { ComponentProps } from 'react';
import { View, Text, Pressable, ScrollView, ActivityIndicator, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { TabBar } from '@/components/TabBar';
import { useEligiblePolicies } from '@/hooks/useEligiblePolicies';
import { useSessionStore } from '@/store/useSessionStore';
import type { EligiblePolicy, UserCriteria } from '@/api/policiesEligible';

type RuleRow = { label: string; value: string; pass: boolean };

function cardIcon(key: string | null): ComponentProps<typeof Ionicons>['name'] {
  if (key === 'monthly') return 'cash-outline';
  if (key === 'jeonse') return 'home-outline';
  if (key === 'hug') return 'shield-checkmark-outline';
  return 'document-text-outline';
}

function fmtWan(v: number): string {
  return v >= 10000 ? `${(v / 10000).toFixed(v % 10000 === 0 ? 0 : 1)}억` : `${v.toLocaleString()}만`;
}

function buildRules(p: EligiblePolicy, c: UserCriteria | null): RuleRow[] {
  if (!c) return [];
  const rules: RuleRow[] = [];
  if (p.age_min != null || p.age_max != null)
    rules.push({ label: `만 나이 ${p.age_min ?? 0}~${p.age_max ?? 99}세`, value: `${c.age}세`, pass: true });
  if (p.income_max_annual != null)
    rules.push({ label: `연소득 ${p.income_max_annual.toLocaleString()}만 이하`, value: `${c.annual_income_wan.toLocaleString()}만`, pass: true });
  if (p.is_homeless_required)
    rules.push({ label: '무주택 세대주', value: '무주택 ✓', pass: true });
  if (p.deposit_limit != null)
    rules.push({ label: `보증금 ${p.deposit_limit.toLocaleString()}만 이하`, value: `${c.deposit_max_wan.toLocaleString()}만`, pass: true });
  if (p.rent_limit != null)
    rules.push({ label: `월세 ${p.rent_limit.toLocaleString()}만 이하`, value: `${c.monthly_rent_max_wan.toLocaleString()}만`, pass: true });
  return rules;
}

function reasonLabel(p: EligiblePolicy): string {
  const cats: string[] = [];
  if (p.age_min != null || p.age_max != null) cats.push('나이');
  if (p.income_max_annual != null) cats.push('소득');
  if (p.is_homeless_required) cats.push('무주택');
  if (p.deposit_limit != null) cats.push('보증금');
  if (p.rent_limit != null) cats.push('월세');
  return cats.length === 0 ? '자격 조건 충족' : `${cats.join('·')} 모든 조건 충족`;
}

function BenefitText({ p }: { p: EligiblePolicy }) {
  const base = { fontSize: 11, color: '#71717A', lineHeight: 15.4, marginBottom: 4 } as const;
  const hi = { color: '#047857', fontWeight: '700' as const };
  if (p.monthly_amount_wan != null) {
    const dur = p.duration_months ?? 12;
    return (
      <Text style={base}>
        월 <Text style={hi}>{p.monthly_amount_wan}만원</Text> × {dur}개월 = 연{' '}
        <Text style={hi}>{(p.monthly_amount_wan * dur).toLocaleString()}만원</Text>
      </Text>
    );
  }
  if (p.loan_limit != null) {
    return (
      <Text style={base}>
        한도 <Text style={hi}>{p.loan_limit.toLocaleString()}만원</Text>
      </Text>
    );
  }
  return <Text style={base} />;
}

function amountStr(p: EligiblePolicy): { amount: string; detail: string } {
  if (p.monthly_amount_wan != null) {
    const dur = p.duration_months ?? 12;
    return { amount: `${(p.monthly_amount_wan * dur).toLocaleString()}만원`, detail: `월 ${p.monthly_amount_wan}만원 × ${dur}개월` };
  }
  if (p.loan_limit != null) return { amount: `${p.loan_limit.toLocaleString()}만원`, detail: '대출·보증 한도' };
  return { amount: '-', detail: '' };
}

function RuleModal({ policy, criteria, userName, onClose }: { policy: EligiblePolicy; criteria: UserCriteria | null; userName: string | null; onClose: () => void }) {
  const rules = buildRules(policy, criteria);
  const { amount, detail } = amountStr(policy);

  return (
    <>
      <Pressable
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(10,10,11,0.5)', zIndex: 20 }}
        onPress={onClose}
      />
      <View style={{ position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: 'white', borderTopLeftRadius: 20, borderTopRightRadius: 20, paddingHorizontal: 16, paddingTop: 12, paddingBottom: 20, zIndex: 21 }}>
        <View style={{ width: 36, height: 4, backgroundColor: '#D4D4D8', borderRadius: 99, alignSelf: 'center', marginBottom: 14 }} />

        <Text style={{ fontSize: 16, fontWeight: '800', color: '#0A0A0B', letterSpacing: -0.32, marginBottom: 4 }}>{policy.name}</Text>
        <Text style={{ fontSize: 11, color: '#71717A', marginBottom: 14 }}>
          {userName ?? ''}님 자격 자동 판정 결과 — <Text style={{ color: '#047857', fontWeight: '700' }}>{rules.length}개 충족</Text>
        </Text>

        <View style={{ backgroundColor: '#ECFDF5', borderWidth: 1, borderColor: '#D1FAE5', borderRadius: 10, padding: 12, marginBottom: 14, alignItems: 'center' }}>
          <Text style={{ fontSize: 10, color: '#047857', fontWeight: '600', marginBottom: 2 }}>예상 수혜 금액</Text>
          <Text style={{ fontSize: 24, fontWeight: '800', color: '#047857', letterSpacing: -0.72 }}>{amount}</Text>
          <Text style={{ fontSize: 10, color: '#059669', marginTop: 2 }}>{detail}</Text>
        </View>

        <View style={{ gap: 4 }}>
          {rules.map((rule, i) => (
            <View key={i} style={{
              flexDirection: 'row', alignItems: 'center', gap: 8,
              paddingHorizontal: 10, paddingVertical: 8, borderRadius: 8,
              backgroundColor: rule.pass ? '#ECFDF5' : '#FEF2F2',
            }}>
              <View style={{ width: 18, height: 18, borderRadius: 9, backgroundColor: rule.pass ? '#10B981' : '#EF4444', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Ionicons name={rule.pass ? 'checkmark' : 'close'} size={10} color="white" />
              </View>
              <Text style={{ flex: 1, fontSize: 11, fontWeight: '500', color: rule.pass ? '#047857' : '#B91C1C' }}>{rule.label}</Text>
              <Text style={{ fontSize: 11, fontWeight: '700', color: rule.pass ? '#047857' : '#B91C1C' }}>{rule.value}</Text>
            </View>
          ))}
        </View>

        <Text style={{ marginTop: 14, fontSize: 9, color: '#A1A1AA', textAlign: 'center' }}>
          {policy.agency_name ? `출처: ${policy.agency_name}` : ''}
        </Text>
      </View>
    </>
  );
}

export default function HsubsidyScreen() {
  const { data: policies, criteria, isLoading, error, needsLogin } = useEligiblePolicies();
  const userName = useSessionStore((s) => s.userName);
  const [activeId, setActiveId] = useState<string | null>(null);

  const list = policies ?? [];
  const activePolicy = list.find((p) => p.id === activeId) ?? null;
  const count = list.length;
  const maxMonthly = list.reduce((m, p) => Math.max(m, p.monthly_amount_wan ?? 0), 0);
  const maxLoan = list.reduce((m, p) => Math.max(m, p.loan_limit ?? 0), 0);
  const heroSub = list.slice(0, 2).map((p) => p.name).join(' + ') + (count > 2 ? ` 외 ${count - 2}건` : '');

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
      {/* AppBar */}
      <View style={{ height: 44, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
        <Pressable onPress={() => router.back()} style={{ width: 30, height: 30, alignItems: 'center', justifyContent: 'center' }}>
          <Ionicons name="chevron-back" size={22} color="#18181B" />
        </Pressable>
        <Text style={{ fontSize: 14, fontWeight: '700', color: '#0A0A0B' }}>지원사업 진단</Text>
        <Pressable style={{ width: 30, height: 30, alignItems: 'center', justifyContent: 'center' }}>
          <Ionicons name="information-circle-outline" size={22} color="#18181B" />
        </Pressable>
      </View>

      {isLoading ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10 }}>
          <ActivityIndicator size="large" color="#10B981" />
          <Text style={{ fontSize: 12, color: '#71717A' }}>자격 판정 중...</Text>
        </View>
      ) : needsLogin ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10, padding: 24 }}>
          <Ionicons name="lock-closed-outline" size={36} color="#A1A1AA" />
          <Text style={{ fontSize: 14, fontWeight: '700', color: '#0A0A0B' }}>로그인이 필요해요</Text>
          <Text style={{ fontSize: 12, color: '#71717A', textAlign: 'center', lineHeight: 18 }}>{'자격 진단 결과는\n로그인 후 확인할 수 있어요.'}</Text>
          <Pressable onPress={() => router.push('/(onboarding)/login' as never)} style={{ marginTop: 8, backgroundColor: '#10B981', borderRadius: 12, paddingVertical: 12, paddingHorizontal: 32 }}>
            <Text style={{ fontSize: 14, fontWeight: '700', color: 'white' }}>로그인</Text>
          </Pressable>
        </View>
      ) : error ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 8, padding: 24 }}>
          <Ionicons name="alert-circle-outline" size={36} color="#DC2626" />
          <Text style={{ fontSize: 13, fontWeight: '700', color: '#DC2626' }}>자격 판정 로드 실패</Text>
          <Text style={{ fontSize: 11, color: '#71717A', textAlign: 'center' }}>먼저 진단을 완료해주세요.</Text>
        </View>
      ) : count === 0 ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 8, padding: 24 }}>
          <Ionicons name="document-text-outline" size={36} color="#A1A1AA" />
          <Text style={{ fontSize: 14, fontWeight: '700', color: '#0A0A0B' }}>받을 수 있는 지원이 없어요</Text>
          <Text style={{ fontSize: 12, color: '#71717A', textAlign: 'center', lineHeight: 18 }}>{'입력하신 조건으로는 매칭되는\n지원사업이 없습니다.'}</Text>
        </View>
      ) : (
        <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 8 }}>
          {/* Hero */}
          <View style={{ margin: 12, borderRadius: 14, padding: 18, backgroundColor: '#0A0A0B', overflow: 'hidden' }}>
            <View style={{ position: 'absolute', top: -30, right: -30, width: 140, height: 140, borderRadius: 70, backgroundColor: 'rgba(255,255,255,0.08)' }} />
            <View style={{ position: 'absolute', bottom: -20, right: -10, width: 100, height: 100, borderRadius: 50, backgroundColor: 'rgba(4,120,87,0.45)' }} />

            <View style={{ position: 'relative', zIndex: 1 }}>
              <View style={{ alignSelf: 'flex-start', backgroundColor: '#6EE7B7', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 4, marginBottom: 8 }}>
                <Text style={{ fontSize: 10, fontWeight: '700', color: '#047857', letterSpacing: 0.4 }}>🎉 모든 자격 충족</Text>
              </View>
              <Text style={{ fontSize: 20, fontWeight: '800', color: 'white', letterSpacing: -0.5, lineHeight: 28, marginBottom: 4 }}>{`${userName ?? ''}님, ${count}가지\n지원을 받을 수 있어요!`}</Text>
              <Text style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)', lineHeight: 18 }}>{heroSub} 모두 가능합니다</Text>

              <View style={{ flexDirection: 'row', gap: 20, marginTop: 14, paddingTop: 14, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.15)' }}>
                {[
                  { value: `${count}종`, label: '자격 충족' },
                  { value: maxMonthly > 0 ? `연 ${(maxMonthly * 12).toLocaleString()}만` : '없음', label: '월 지원금' },
                  { value: maxLoan > 0 ? `${fmtWan(maxLoan)}` : '없음', label: '대출 한도' },
                ].map((stat) => (
                  <View key={stat.label}>
                    <Text style={{ fontSize: 20, fontWeight: '800', color: 'white', letterSpacing: -0.6 }}>{stat.value}</Text>
                    <Text style={{ fontSize: 10, color: 'rgba(255,255,255,0.7)', marginTop: 2 }}>{stat.label}</Text>
                  </View>
                ))}
              </View>
            </View>
          </View>

          {/* Section header */}
          <View style={{ paddingHorizontal: 16, paddingTop: 16, paddingBottom: 10, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <Text style={{ fontSize: 14, fontWeight: '700', color: '#0A0A0B' }}>자격 진단 결과</Text>
            <Text style={{ fontSize: 11, color: '#71717A' }}>{count} / {count} 가능</Text>
          </View>

          {/* Eligibility cards */}
          <View style={{ paddingHorizontal: 16, gap: 8, paddingBottom: 16 }}>
            {list.map((p) => (
              <View
                key={p.id}
                style={{
                  borderRadius: 12, backgroundColor: 'white',
                  borderWidth: 1, borderColor: '#E4E4E7',
                  borderLeftWidth: 4, borderLeftColor: '#10B981',
                  overflow: 'hidden', flexDirection: 'row',
                }}
              >
                {/* 자격 정보 영역 — 탭하면 상세 모달 */}
                <Pressable onPress={() => setActiveId(p.id)} style={{ flex: 1, padding: 14, gap: 12, flexDirection: 'row' }}>
                  <View style={{ width: 40, height: 40, borderRadius: 10, backgroundColor: '#ECFDF5', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Ionicons name={cardIcon(p.card_key)} size={20} color="#047857" />
                  </View>

                  <View style={{ flex: 1, minWidth: 0 }}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13, fontWeight: '700', color: '#0A0A0B', letterSpacing: -0.13, flex: 1, marginRight: 8 }} numberOfLines={1}>{p.name}</Text>
                      <View style={{ backgroundColor: '#ECFDF5', paddingHorizontal: 7, paddingVertical: 2, borderRadius: 4 }}>
                        <Text style={{ fontSize: 9, fontWeight: '700', color: '#047857', letterSpacing: 0.36 }}>✓ 가능</Text>
                      </View>
                    </View>
                    <BenefitText p={p} />
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4, paddingTop: 6, borderTopWidth: 1, borderTopColor: '#ECFDF5' }}>
                      <Ionicons name="checkmark" size={12} color="#047857" />
                      <Text style={{ fontSize: 10, color: '#047857', flex: 1, lineHeight: 14 }}>{reasonLabel(p)}</Text>
                    </View>
                  </View>
                </Pressable>

                {/* 우측 화살표 — 신청 링크로 이동 */}
                <Pressable
                  onPress={() => p.apply_url && Linking.openURL(p.apply_url)}
                  style={{ width: 56, alignItems: 'center', justifyContent: 'center', backgroundColor: '#10B981' }}
                >
                  <Ionicons name="open-outline" size={20} color="white" />
                </Pressable>
              </View>
            ))}
          </View>
        </ScrollView>
      )}

      <TabBar />

      {activePolicy && <RuleModal policy={activePolicy} criteria={criteria} userName={userName} onClose={() => setActiveId(null)} />}
    </SafeAreaView>
  );
}
