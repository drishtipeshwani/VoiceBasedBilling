import { Pressable, Text } from 'react-native';
import InvoiceComposer from '../components/InvoiceComposer';
import { styles } from '../components/InvoiceComposer.styles';
import { useAuth } from '../utils/authContext';

export default function HomeScreen() {
  const { lock } = useAuth();

  return (
    <InvoiceComposer
      headerAccessory={
        <Pressable
          onPress={lock}
          accessibilityLabel="Lock app"
          style={({ pressed }) => [
            styles.signOutButton,
            pressed && styles.signOutButtonPressed,
          ]}
        >
          <Text style={styles.signOutText}>Lock</Text>
        </Pressable>
      }
    />
  );
}
