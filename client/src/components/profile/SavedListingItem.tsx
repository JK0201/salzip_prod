import { View, Text, Pressable, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { FavoriteItem } from '@/api/favorites';
import { listingThumb } from '@/constants/listingImages';

type Props = {
  listing: FavoriteItem;
  isSaved: boolean;
  onPress: () => void;
  onToggleSave: () => void;
};

export function SavedListingItem({ listing, isSaved, onPress, onToggleSave }: Props) {
  const danger = listing.risk_level === 'danger';
  const depositLabel =
    listing.deposit >= 10000
      ? `${(listing.deposit / 10000).toFixed(listing.deposit % 10000 === 0 ? 0 : 1)}억`
      : `${listing.deposit.toLocaleString()}만`;

  return (
    <Pressable
      onPress={onPress}
      className="flex-row gap-3 rounded-xl border border-neutral-200 bg-white p-3.5"
    >
      <View className="h-20 w-20 rounded-xl overflow-hidden bg-neutral-100">
        <Image source={listingThumb(listing.listing_id)} style={{ width: 80, height: 80 }} resizeMode="cover" />
      </View>

      <View className="flex-1">
        <Text className="text-xs text-neutral-400">
          {(listing.estimated_kind ?? listing.kind)}
          {listing.umd_name ? ` · ${listing.umd_name}` : ''}
        </Text>
        <Text className="mt-1 text-[15px] font-bold text-neutral-900">
          보증 <Text className="font-extrabold">{depositLabel}</Text>
          {listing.monthly_rent > 0 ? (
            <>
              {' '}/ 월 <Text className="font-extrabold">{listing.monthly_rent}만</Text>
            </>
          ) : (
            <Text className="font-extrabold"> · 전세</Text>
          )}
        </Text>
        <Text className="mt-1 text-xs text-neutral-400">
          {listing.area_m2 != null ? `${listing.area_m2}㎡` : '-'}
          {listing.floor != null ? ` · ${listing.floor}층` : ''}
          {listing.build_year != null ? ` · ${listing.build_year}년` : ''}
        </Text>

        <View className="mt-2 flex-row gap-1.5">
          <View
            className={`flex-row items-center gap-1 rounded px-2 py-0.5 ${danger ? 'bg-red-50' : 'bg-emerald-50'}`}
          >
            <View className={`h-1.5 w-1.5 rounded-full ${danger ? 'bg-red-500' : 'bg-emerald-500'}`} />
            <Text className={`text-[11px] font-semibold ${danger ? 'text-red-800' : 'text-emerald-700'}`}>
              {danger ? '침수 이력' : '안전'}
            </Text>
          </View>
        </View>
      </View>

      <Pressable onPress={onToggleSave} hitSlop={8} className="self-start p-1">
        <Ionicons name={isSaved ? 'heart' : 'heart-outline'} size={20} color={isSaved ? '#EF4444' : '#A1A1AA'} />
      </Pressable>
    </Pressable>
  );
}
