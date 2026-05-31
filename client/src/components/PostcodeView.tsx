import { MapHtmlView } from '@/components/MapHtmlView';

type PostcodeResult = {
  roadAddress: string;
  jibunAddress: string;
  zonecode: string;
};

type Props = {
  onSelect: (result: PostcodeResult) => void;
};

const HTML = `<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body,#postcode{width:100%;height:100%}
</style>
<script src="https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js"></script>
</head>
<body>
<div id="postcode"></div>
<script>
function send(data){
  var msg=JSON.stringify({
    type:'address',
    roadAddress:data.roadAddress||'',
    jibunAddress:data.jibunAddress||data.autoJibunAddress||'',
    zonecode:data.zonecode||''
  });
  if(window.ReactNativeWebView){window.ReactNativeWebView.postMessage(msg);}
  else if(window.parent){window.parent.postMessage(msg,'*');}
}
window.addEventListener('load',function(){
  new daum.Postcode({
    oncomplete:send,
    width:'100%',
    height:'100%'
  }).embed(document.getElementById('postcode'),{autoClose:false});
});
</script>
</body>
</html>`;

export function PostcodeView({ onSelect }: Props) {
  const handleMessage = (data: string) => {
    try {
      const msg = JSON.parse(data) as { type: string } & PostcodeResult;
      if (msg.type === 'address') {
        onSelect({
          roadAddress: msg.roadAddress,
          jibunAddress: msg.jibunAddress,
          zonecode: msg.zonecode,
        });
      }
    } catch {}
  };

  return <MapHtmlView html={HTML} onMessage={handleMessage} />;
}
