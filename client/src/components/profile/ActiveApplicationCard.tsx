import { View, Text } from 'react-native';
import type { ActiveApplication } from '@/types/profile';

type Props = {
  application: ActiveApplication;
};

export function ActiveApplicationCard({ application }: Props) {
  const percent = Math.round(
    (application.currentStep / application.totalSteps) * 100
  );

  return (
    <View className="rounded-2xl border-[1.5px] border-emerald-500 bg-white p-4">
      <View className="flex-row items-center">
        <View className="h-10 w-10 items-center justify-center rounded-xl bg-emerald-50">
          <Text className="text-lg">{application.programIcon}</Text>
        </View>

        <Text className="ml-3 flex-1 text-base font-bold text-neutral-900">
          {application.programName}
        </Text>

        <View className="rounded-full bg-emerald-50 px-2.5 py-1">
          <Text className="text-[11px] font-bold text-emerald-700">
            {application.status}
          </Text>
        </View>
      </View>

      <View className="mt-4 flex-row items-end justify-between">
        <Text className="text-sm font-semibold text-neutral-600">
          단계 진행{' '}
          <Text className="font-extrabold text-emerald-700">
            {application.currentStep} / {application.totalSteps}
          </Text>
        </Text>
        <Text className="text-lg font-extrabold text-emerald-700">{percent}%</Text>
      </View>

      <View className="mt-2 h-1.5 overflow-hidden rounded-full bg-neutral-100">
        <View
          className="h-full rounded-full bg-emerald-500"
          style={{ width: `${percent}%` }}
        />
      </View>

      <View className="mt-3.5 flex-row items-center rounded-xl bg-neutral-50 p-3">
        <View className="flex-1">
          <Text className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
            다음 할 일
          </Text>
          <Text className="mt-0.5 text-sm font-semibold text-neutral-900">
            {application.nextTask}
          </Text>
        </View>
        <Text className="text-xs font-bold text-red-500">
          D-{application.daysLeft}
        </Text>
      </View>
    </View>
  );
}
