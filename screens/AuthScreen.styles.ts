import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5F6FA',
  },
  flex: {
    flex: 1,
  },
  scrollContent: {
    padding: 24,
    paddingTop: 48,
    flexGrow: 1,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1C1C28',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#6E6E80',
    textAlign: 'center',
    marginTop: 6,
    marginBottom: 24,
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    color: '#1C1C28',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EC',
  },
  pinInput: {
    marginTop: 16,
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EC',
  },
  switchLabel: {
    fontSize: 15,
    color: '#1C1C28',
    fontWeight: '500',
  },
  hintText: {
    fontSize: 13,
    color: '#6E6E80',
    marginBottom: 12,
    textAlign: 'center',
  },
  errorText: {
    color: '#D64545',
    fontSize: 13,
    marginBottom: 12,
    textAlign: 'center',
  },
  primaryButton: {
    backgroundColor: '#4C6FFF',
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    marginTop: 4,
  },
  primaryButtonPressed: {
    opacity: 0.85,
  },
  primaryButtonDisabled: {
    opacity: 0.7,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  linkButton: {
    marginTop: 16,
    alignItems: 'center',
  },
  linkText: {
    color: '#4C6FFF',
    fontSize: 13,
    fontWeight: '500',
  },
});
