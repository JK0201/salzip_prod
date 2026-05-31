import { useEffect, useRef } from 'react';
import { View, type ViewStyle, type StyleProp } from 'react-native';
import { WebView, type WebViewMessageEvent } from 'react-native-webview';

type Props = {
  html: string;
  onMessage: (data: string) => void;
  outbound?: string | null;
  style?: StyleProp<ViewStyle>;
};

export function MapHtmlView({ html, onMessage, outbound, style }: Props) {
  const ref = useRef<WebView>(null);

  useEffect(() => {
    if (outbound == null) return;
    ref.current?.injectJavaScript(
      `window.__deliver && window.__deliver(${JSON.stringify(outbound)}); true;`
    );
  }, [outbound]);

  return (
    <View style={[{ flex: 1 }, style]}>
      <WebView
        ref={ref}
        source={{ html, baseUrl: 'https://localhost' }}
        style={{ flex: 1 }}
        originWhitelist={['*']}
        javaScriptEnabled
        domStorageEnabled
        mixedContentMode="compatibility"
        onMessage={(e: WebViewMessageEvent) => onMessage(e.nativeEvent.data)}
        scrollEnabled={false}
        webviewDebuggingEnabled
      />
    </View>
  );
}
