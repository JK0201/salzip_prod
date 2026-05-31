import { KeyboardAvoidingView, Platform, Pressable, Text, View } from 'react-native';
import type { ReactNode } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  step: number;
  barTitle?: string;
  onBack?: () => void;
  onClose?: () => void;
  children: ReactNode;
  footer?: ReactNode;
}

export function DiagnosisShell({ step, barTitle = '라이프 프로파일', onBack, onClose, children, footer }: Props) {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
      {/* 앱 바 */}
      <View className="h-11 px-[14px] flex-row items-center justify-between">
        {onBack
          ? <Pressable onPress={onBack} className="w-10 h-10 items-center justify-center active:opacity-50">
              <Ionicons name="chevron-back" size={22} color="#18181B" />
            </Pressable>
          : <View className="w-10" />}
        <Text className="text-[15px] font-bold tracking-[-0.15px] text-[#0A0A0B]">{barTitle}</Text>
        {onClose
          ? <Pressable onPress={onClose} className="w-10 h-10 items-center justify-center active:opacity-50">
              <Ionicons name="close" size={22} color="#18181B" />
            </Pressable>
          : <View className="w-10" />}
      </View>

      {/* 진행률 */}
      <View className="px-5 flex-row items-center gap-2 pt-4 mb-4">
        <View className="flex-1 h-1 bg-[#E4E4E7] rounded-full overflow-hidden">
          <View className="h-full bg-[#10B981] rounded-full" style={{ width: `${(step / 5) * 100}%` }} />
        </View>
        <Text className="text-[11px] font-bold text-[#71717A] tracking-[0.05em]">{step} / 5</Text>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={0}
      >
        <View className="flex-1 px-5 pb-5">
          {children}
        </View>
      </KeyboardAvoidingView>

      {footer && (
        <View className="px-5 pb-5" style={{ transform: [{ translateY: -36 }] }}>
          {footer}
        </View>
      )}
    </SafeAreaView>
  );
}
