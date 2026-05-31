// 멀티 에이전트 토큰 스트리밍 흉내. visible=true 시점부터 chunks 순차 append.
// chunk 단위 (글자 or 문장)로 delay마다 추가. 완료 시 onDone.
import { useEffect, useRef, useState } from 'react';

export function useMockStream(
  visible: boolean,
  full: string,
  opts?: { chunkSize?: number; delayMs?: number; startDelayMs?: number; onDone?: () => void },
) {
  const chunkSize = opts?.chunkSize ?? 4;
  const delayMs = opts?.delayMs ?? 18;
  const startDelayMs = opts?.startDelayMs ?? 200;
  const [text, setText] = useState('');
  const [done, setDone] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!visible) {
      setText('');
      setDone(false);
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }
    let i = 0;
    const start = setTimeout(() => {
      timerRef.current = setInterval(() => {
        i += chunkSize;
        if (i >= full.length) {
          setText(full);
          setDone(true);
          opts?.onDone?.();
          if (timerRef.current) clearInterval(timerRef.current);
          return;
        }
        setText(full.slice(0, i));
      }, delayMs);
    }, startDelayMs);
    return () => {
      clearTimeout(start);
      if (timerRef.current) clearInterval(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, full]);

  return { text, done };
}
