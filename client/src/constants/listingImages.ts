import type { ImageSourcePropType } from 'react-native';

// Metro 번들러는 require() 경로가 정적이어야 합니다 — 동적 생성 불가

export const VILLA_IMAGES: ImageSourcePropType[] = [
  require('../../assets/images/listings/villa/villa1.webp'),
  require('../../assets/images/listings/villa/villa2.webp'),
  require('../../assets/images/listings/villa/villa3.webp'),
  require('../../assets/images/listings/villa/villa4.webp'),
  require('../../assets/images/listings/villa/villa5.webp'),
];

export const OFFICETEL_IMAGES: ImageSourcePropType[] = [
  require('../../assets/images/listings/officetel/officetel1.webp'),
  require('../../assets/images/listings/officetel/officetel2.webp'),
  require('../../assets/images/listings/officetel/officetel3.webp'),
  require('../../assets/images/listings/officetel/officetel4.webp'),
  require('../../assets/images/listings/officetel/officetel5.webp'),
];

export const ONEROOM_IMAGES: ImageSourcePropType[] = [
  require('../../assets/images/listings/oneroom/oneroom1.webp'),
  require('../../assets/images/listings/oneroom/oneroom2.webp'),
  require('../../assets/images/listings/oneroom/oneroom3.webp'),
  require('../../assets/images/listings/oneroom/oneroom4.webp'),
  require('../../assets/images/listings/oneroom/oneroom5.webp'),
];

// 실매물 id는 UUID라 정적 매핑 불가 → id 해시로 결정론적 선택.
// 같은 id면 어디서 보든(지도 하단·검색 리스트·상세·저장) 항상 같은 사진.
const ALL_IMAGES: ImageSourcePropType[] = [
  ...VILLA_IMAGES,
  ...OFFICETEL_IMAGES,
  ...ONEROOM_IMAGES,
];

function hashId(id: string): number {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return h;
}

export function listingThumb(id: string): ImageSourcePropType {
  return ALL_IMAGES[hashId(id) % ALL_IMAGES.length];
}

export function listingDetailImages(id: string): ImageSourcePropType[] {
  const base = hashId(id) % ALL_IMAGES.length;
  return [0, 1, 2].map((o) => ALL_IMAGES[(base + o) % ALL_IMAGES.length]);
}
