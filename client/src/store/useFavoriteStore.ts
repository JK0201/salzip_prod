import { create } from 'zustand';

import { addFavorite, getFavorites, removeFavorite } from '@/api/favorites';

interface FavoriteState {
  ids: Set<string>;
  loaded: boolean;
  load: () => Promise<void>;
  toggle: (listingId: string) => Promise<void>;
  has: (listingId: string) => boolean;
  clear: () => void;
}

export const useFavoriteStore = create<FavoriteState>((set, get) => ({
  ids: new Set(),
  loaded: false,

  load: async () => {
    try {
      const { ids } = await getFavorites();
      set({ ids: new Set(ids), loaded: true });
    } catch (e) {
      console.log('[favorite] load 실패', e);
    }
  },

  toggle: async (listingId) => {
    const had = get().ids.has(listingId);
    // 낙관적 갱신
    set((s) => {
      const next = new Set(s.ids);
      had ? next.delete(listingId) : next.add(listingId);
      return { ids: next };
    });
    try {
      if (had) await removeFavorite(listingId);
      else await addFavorite(listingId);
    } catch (e) {
      // 실패 시 롤백
      set((s) => {
        const next = new Set(s.ids);
        had ? next.add(listingId) : next.delete(listingId);
        return { ids: next };
      });
      console.log('[favorite] toggle 실패', e);
    }
  },

  has: (listingId) => get().ids.has(listingId),

  clear: () => set({ ids: new Set(), loaded: false }),
}));
