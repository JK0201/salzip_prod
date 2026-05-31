import { useEffect, useRef } from 'react';
import { View } from 'react-native';

type PostcodeResult = {
  roadAddress: string;
  jibunAddress: string;
  zonecode: string;
};

type Props = {
  onSelect: (result: PostcodeResult) => void;
};

export function PostcodeView({ onSelect }: Props) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  useEffect(() => {
    const handler = (e: MessageEvent) => {
      if (iframeRef.current && e.source !== iframeRef.current.contentWindow) return;
      try {
        const msg = JSON.parse(typeof e.data === 'string' ? e.data : JSON.stringify(e.data)) as {
          type: string;
        } & PostcodeResult;
        console.log('[PostcodeView.web] parsed', msg);
        if (msg.type === 'address') {
          onSelect({
            roadAddress: msg.roadAddress,
            jibunAddress: msg.jibunAddress,
            zonecode: msg.zonecode,
          });
        }
      } catch {}
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, [onSelect]);

  return (
    <View style={{ flex: 1 }}>
      <iframe
        ref={iframeRef}
        src="/postcode.html"
        style={{ width: '100%', height: '100%', border: 0, display: 'block' }}
      />
    </View>
  );
}
