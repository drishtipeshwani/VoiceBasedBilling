import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../utils/authContext';
import { styles } from './AuthScreen.styles';

type AuthMethod = 'email' | 'phone';
type Mode = 'signIn' | 'signUp';

export default function AuthScreen() {
  const { signInWithPassword, signUpWithPassword, sendPhoneOtp, verifyPhoneOtp } = useAuth();

  const [authMethod, setAuthMethod] = useState<AuthMethod>('email');
  const [mode, setMode] = useState<Mode>('signIn');

  const [name, setName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [otpSent, setOtpSent] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  const resetMessages = () => {
    setErrorMessage(null);
    setInfoMessage(null);
  };

  const switchAuthMethod = (method: AuthMethod) => {
    resetMessages();
    setOtpSent(false);
    setOtpCode('');
    setAuthMethod(method);
  };

  const switchMode = (nextMode: Mode) => {
    resetMessages();
    setOtpSent(false);
    setOtpCode('');
    setMode(nextMode);
  };

  const handleEmailSubmit = async () => {
    resetMessages();

    if (!email.trim()) {
      setErrorMessage('Please enter your email.');
      return;
    }
    if (!password) {
      setErrorMessage('Please enter your password.');
      return;
    }
    if (mode === 'signUp' && !name.trim()) {
      setErrorMessage('Please enter your name.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (mode === 'signIn') {
        const { error } = await signInWithPassword(email.trim(), password);
        if (error) setErrorMessage(error);
      } else {
        const { error, needsEmailConfirmation } = await signUpWithPassword(
          email.trim(),
          password,
          name.trim(),
          companyName.trim(),
        );
        if (error) {
          setErrorMessage(error);
        } else if (needsEmailConfirmation) {
          setInfoMessage('Check your email to confirm your account before signing in.');
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSendOtp = async () => {
    resetMessages();

    if (!phone.trim()) {
      setErrorMessage('Please enter your phone number, e.g. +919876543210.');
      return;
    }
    if (mode === 'signUp' && !name.trim()) {
      setErrorMessage('Please enter your name.');
      return;
    }

    setIsSubmitting(true);
    try {
      const { error } = await sendPhoneOtp(
        phone.trim(),
        mode === 'signUp' ? name.trim() : undefined,
        mode === 'signUp' ? companyName.trim() : undefined,
      );
      if (error) {
        setErrorMessage(error);
      } else {
        setOtpSent(true);
        setInfoMessage(`We sent a code to ${phone.trim()}.`);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyOtp = async () => {
    resetMessages();

    if (!otpCode.trim()) {
      setErrorMessage('Please enter the code you received.');
      return;
    }

    setIsSubmitting(true);
    try {
      const { error } = await verifyPhoneOtp(phone.trim(), otpCode.trim());
      if (error) setErrorMessage(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChangePhone = () => {
    resetMessages();
    setOtpSent(false);
    setOtpCode('');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <Text style={styles.title}>Voice Invoice</Text>
          <Text style={styles.subtitle}>
            {mode === 'signIn' ? 'Sign in to continue' : 'Create an account to get started'}
          </Text>

          <View style={styles.methodToggle}>
            <Pressable
              onPress={() => switchAuthMethod('email')}
              style={[styles.methodTab, authMethod === 'email' && styles.methodTabActive]}
            >
              <Text style={[styles.methodTabText, authMethod === 'email' && styles.methodTabTextActive]}>
                Email
              </Text>
            </Pressable>
            <Pressable
              onPress={() => switchAuthMethod('phone')}
              style={[styles.methodTab, authMethod === 'phone' && styles.methodTabActive]}
            >
              <Text style={[styles.methodTabText, authMethod === 'phone' && styles.methodTabTextActive]}>
                Phone
              </Text>
            </Pressable>
          </View>

          {authMethod === 'email' ? (
            <>
              {mode === 'signUp' ? (
                <>
                  <TextInput
                    style={styles.input}
                    placeholder="Name"
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
                </>
              ) : null}

              <TextInput
                style={styles.input}
                placeholder="Email"
                placeholderTextColor="#A0A0B2"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="email-address"
              />

              <TextInput
                style={styles.input}
                placeholder="Password"
                placeholderTextColor="#A0A0B2"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />

              {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
              {infoMessage ? <Text style={styles.infoText}>{infoMessage}</Text> : null}

              <Pressable
                onPress={handleEmailSubmit}
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
                  <Text style={styles.primaryButtonText}>{mode === 'signIn' ? 'Sign In' : 'Sign Up'}</Text>
                )}
              </Pressable>
            </>
          ) : (
            <>
              {!otpSent ? (
                <>
                  {mode === 'signUp' ? (
                    <>
                      <TextInput
                        style={styles.input}
                        placeholder="Name"
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
                    </>
                  ) : null}

                  <TextInput
                    style={styles.input}
                    placeholder="Phone number, e.g. +919876543210"
                    placeholderTextColor="#A0A0B2"
                    value={phone}
                    onChangeText={setPhone}
                    autoCapitalize="none"
                    autoCorrect={false}
                    keyboardType="phone-pad"
                  />

                  {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
                  {infoMessage ? <Text style={styles.infoText}>{infoMessage}</Text> : null}

                  <Pressable
                    onPress={handleSendOtp}
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
                      <Text style={styles.primaryButtonText}>Send Code</Text>
                    )}
                  </Pressable>
                </>
              ) : (
                <>
                  <TextInput
                    style={styles.input}
                    placeholder="Enter code"
                    placeholderTextColor="#A0A0B2"
                    value={otpCode}
                    onChangeText={setOtpCode}
                    keyboardType="number-pad"
                  />

                  {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
                  {infoMessage ? <Text style={styles.infoText}>{infoMessage}</Text> : null}

                  <Pressable
                    onPress={handleVerifyOtp}
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
                      <Text style={styles.primaryButtonText}>Verify</Text>
                    )}
                  </Pressable>

                  <Pressable onPress={handleChangePhone} style={styles.linkButton}>
                    <Text style={styles.linkText}>Use a different phone number</Text>
                  </Pressable>
                </>
              )}
            </>
          )}

          <Pressable onPress={() => switchMode(mode === 'signUp' ? 'signIn' : 'signUp')} style={styles.linkButton}>
            <Text style={styles.linkText}>
              {mode === 'signUp' ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
            </Text>
          </Pressable>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
