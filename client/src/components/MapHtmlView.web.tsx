import { useEffect, useRef, useState } from 'react';
import { View, type ViewStyle, type StyleProp } from 'react-native';

type Props = {
  html: string;
  onMessage: (data: string) => void;
  outbound?: string | null;
  style?: StyleProp<ViewStyle>;
};

export function MapHtmlView({ html, onMessage, outbound, style }: Props) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const handler = (e: MessageEvent) => {
      if (iframeRef.current && e.source !== iframeRef.current.contentWindow) return;
      const data = typeof e.data === 'string' ? e.data : JSON.stringify(e.data);
      onMessage(data);
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, [onMessage]);

  useEffect(() => {
    if (outbound == null) return;
    iframeRef.current?.contentWindow?.postMessage(outbound, '*');
  }, [outbound]);

  return (
    <View style={[{ flex: 1 }, style]}>
      <iframe
        ref={iframeRef}
        srcDoc={mounted ? html : undefined}
        style={{ width: '100%', height: '100%', border: 0, display: 'block' }}
      />
    </View>
  );
}
