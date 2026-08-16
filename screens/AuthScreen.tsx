import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../utils/authContext';
import { styles } from './AuthScreen.styles';

export default function AuthScreen() {
  const {
    hasRegisteredUser,
    biometricAvailable,
    biometricEnabled,
    register,
    unlockWithBiometrics,
    unlockWithPin,
  } = useAuth();

  if (!hasRegisteredUser) {
    return (
      <RegisterForm
        biometricAvailable={biometricAvailable}
        onRegister={register}
      />
    );
  }

  return (
    <UnlockForm
      biometricAvailable={biometricAvailable}
      biometricEnabled={biometricEnabled}
      onUnlockBiometrics={unlockWithBiometrics}
      onUnlockPin={unlockWithPin}
    />
  );
}

function RegisterForm({
  biometricAvailable,
  onRegister,
}: {
  biometricAvailable: boolean;
  onRegister: ReturnType<typeof useAuth>['register'];
}) {
  const [name, setName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [enableBiometrics, setEnableBiometrics] = useState(biometricAvailable);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setEnableBiometrics(biometricAvailable);
  }, [biometricAvailable]);

  const handleSubmit = async () => {
    setErrorMessage(null);
    if (pin !== confirmPin) {
      setErrorMessage('PINs do not match.');
      return;
    }

    setIsSubmitting(true);
    try {
      const { error } = await onRegister({
        name,
        companyName,
        email: email.trim() || null,
        phone: phone.trim() || null,
        pin,
        enableBiometrics,
      });
      if (error) setErrorMessage(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <Text style={styles.title}>Voice Invoice</Text>
          <Text style={styles.subtitle}>Set up this phone for your shop</Text>

          <TextInput
            style={styles.input}
            placeholder="Your name"
            placeholderTextColor="#A0A0B2"
            value={name}
            onChangeText={setName}
            autoCapitalize="words"
          />
          <TextInput
            style={styles.input}
            placeholder="Company name"
            placeholderTextColor="#A0A0B2"
            value={companyName}
            onChangeText={setCompanyName}
            autoCapitalize="words"
          />
          <TextInput
            style={styles.input}
            placeholder="Email (optional)"
            placeholderTextColor="#A0A0B2"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="email-address"
          />
          <TextInput
            style={styles.input}
            placeholder="Phone (optional)"
            placeholderTextColor="#A0A0B2"
            value={phone}
            onChangeText={setPhone}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="phone-pad"
          />
          <TextInput
            style={styles.input}
            placeholder="PIN (4–6 digits)"
            placeholderTextColor="#A0A0B2"
            value={pin}
            onChangeText={setPin}
            keyboardType="number-pad"
            maxLength={6}
            secureTextEntry
          />
          <TextInput
            style={styles.input}
            placeholder="Confirm PIN"
            placeholderTextColor="#A0A0B2"
            value={confirmPin}
            onChangeText={setConfirmPin}
            keyboardType="number-pad"
            maxLength={6}
            secureTextEntry
          />

          {biometricAvailable ? (
            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Unlock with Face ID</Text>
              <Switch
                value={enableBiometrics}
                onValueChange={setEnableBiometrics}
                trackColor={{ false: '#E5E5EC', true: '#4C6FFF' }}
              />
            </View>
          ) : (
            <Text style={styles.hintText}>
              Face ID is not available on this device. You will unlock with your PIN.
            </Text>
          )}

          {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}

          <Pressable
            onPress={handleSubmit}
            disabled={isSubmitting}
            style={({ pressed }) => [
              styles.primaryButton,
              pressed && styles.primaryButtonPressed,
              isSubmitting && styles.primaryButtonDisabled,
            ]}
          >
            {isSubmitting ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.primaryButtonText}>Create shop</Text>
            )}
          </Pressable>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function UnlockForm({
  biometricAvailable,
  biometricEnabled,
  onUnlockBiometrics,
  onUnlockPin,
}: {
  biometricAvailable: boolean;
  biometricEnabled: boolean;
  onUnlockBiometrics: ReturnType<typeof useAuth>['unlockWithBiometrics'];
  onUnlockPin: ReturnType<typeof useAuth>['unlockWithPin'];
}) {
  const [pin, setPin] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showPin, setShowPin] = useState(!(biometricEnabled && biometricAvailable));
  const autoPrompted = useRef(false);

  useEffect(() => {
    if (autoPrompted.current || !biometricEnabled || !biometricAvailable) {
      return;
    }
    autoPrompted.current = true;
    void onUnlockBiometrics().then(({ error }) => {
      if (error) {
        setShowPin(true);
        setErrorMessage(error);
      }
    });
  }, [biometricAvailable, biometricEnabled, onUnlockBiometrics]);

  const handlePinUnlock = async () => {
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      const { error } = await onUnlockPin(pin);
      if (error) setErrorMessage(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFaceId = async () => {
    setErrorMessage(null);
    const { error } = await onUnlockBiometrics();
    if (error) {
      setShowPin(true);
      setErrorMessage(error);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <Text style={styles.title}>Voice Invoice</Text>
          <Text style={styles.subtitle}>Unlock to open your shop</Text>

          {biometricEnabled && biometricAvailable ? (
            <Pressable
              onPress={handleFaceId}
              style={({ pressed }) => [
                styles.primaryButton,
                pressed && styles.primaryButtonPressed,
              ]}
            >
              <Text style={styles.primaryButtonText}>Unlock with Face ID</Text>
            </Pressable>
          ) : null}

          {showPin ? (
            <>
              <TextInput
                style={[styles.input, styles.pinInput]}
                placeholder="PIN"
                placeholderTextColor="#A0A0B2"
                value={pin}
                onChangeText={setPin}
                keyboardType="number-pad"
                maxLength={6}
                secureTextEntry
              />
              {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
              <Pressable
                onPress={handlePinUnlock}
                disabled={isSubmitting}
                style={({ pressed }) => [
                  styles.primaryButton,
                  pressed && styles.primaryButtonPressed,
                  isSubmitting && styles.primaryButtonDisabled,
                ]}
              >
                {isSubmitting ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <Text style={styles.primaryButtonText}>Unlock</Text>
                )}
              </Pressable>
            </>
          ) : (
            <>
              {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
              <Pressable onPress={() => setShowPin(true)} style={styles.linkButton}>
                <Text style={styles.linkText}>Use PIN</Text>
              </Pressable>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
