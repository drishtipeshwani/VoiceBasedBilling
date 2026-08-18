import { useEffect } from 'react';
import { ActivityIndicator, Pressable, Text } from 'react-native';
import Animated, {
  interpolateColor,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';
import { styles } from './SaveButton.styles';

interface SaveButtonProps {
  onPress: () => void;
  isSaving: boolean;
}

export default function SaveButton({ onPress, isSaving }: SaveButtonProps) {
  const saving = useSharedValue(0);
  const pressed = useSharedValue(0);

  useEffect(() => {
    saving.value = withTiming(isSaving ? 1 : 0, { duration: 160 });
  }, [isSaving, saving]);

  const animatedStyle = useAnimatedStyle(() => {
    const t = Math.max(pressed.value, saving.value);
    return {
      transform: [{ scale: 1 - t * 0.08 }],
      backgroundColor: interpolateColor(t, [0, 1], ['#FFFFFF', '#4C6FFF']),
    };
  });

  return (
    <Pressable
      onPress={onPress}
      disabled={isSaving}
      accessibilityRole="button"
      accessibilityLabel="Save"
      accessibilityState={{ busy: isSaving, disabled: isSaving }}
      onPressIn={() => {
        pressed.value = withTiming(1, { duration: 80 });
      }}
      onPressOut={() => {
        pressed.value = withTiming(0, { duration: 120 });
      }}
    >
      <Animated.View style={[styles.button, animatedStyle]}>
        {isSaving ? (
          <ActivityIndicator size="small" color="#FFFFFF" />
        ) : (
          <Text style={styles.text}>Save</Text>
        )}
      </Animated.View>
    </Pressable>
  );
}
