// Route: /(main)/_layout (탭 네비게이터)
import { Tabs } from 'expo-router';

export default function MainLayout() {
  return (
    <Tabs screenOptions={{ headerShown: false, tabBarStyle: { display: 'none' } }}>
      <Tabs.Screen name="hsubsidy" />
      <Tabs.Screen name="mypage" />
    </Tabs>
  );
}
