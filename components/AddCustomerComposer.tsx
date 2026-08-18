import { useCallback, useEffect, useRef, useState } from 'react';
import { Text, View } from 'react-native';
import { useSQLiteContext } from 'expo-sqlite';
import VoiceComposer from './VoiceComposer';
import { CUSTOMER_SYSTEM_PROMPT_SHORT } from '../utils/customerSystemPrompt';
import {
  DuplicateNameError,
  SaveRecordError,
  insertCustomer,
} from '../db/queries';
import type { CustomerDraft } from '../types/ledger';
import { emptyCustomerDraft } from '../types/ledger';
import {
  CustomerAgentActionResponseSchema,
  type CustomerAgentActionResponse,
} from '../types/agentActionResponse';
import { useAuth } from '../utils/authContext';
import {
  applyCustomerAction,
  describeCustomerAction,
  isIncompleteCustomerAction,
  isSaveCustomerAction,
  isUnknownCustomerAction,
} from '../utils/applyCustomerAction';
import { formatAmount } from '../utils/currency';
import { useShopData } from '../utils/shopDataContext';
import { waitForSaveFeedback } from '../utils/saveFeedback';
import { useVoiceAgent } from '../utils/useVoiceAgent';
import { styles } from '../screens/LedgerScreen.styles';

function CustomerDraftCard({ draft }: { draft: CustomerDraft }) {
  const hasBalance = draft.balanceAmount != null;
  const isSettled = (draft.balanceAmount ?? 0) <= 0;
  return (
    <View style={styles.row}>
      <Text style={draft.name ? styles.customerName : styles.placeholderName}>
        {draft.name || 'Customer name'}
      </Text>
      <View style={styles.balanceWrap}>
        <Text
          style={[
            hasBalance ? styles.balance : styles.placeholderBalance,
            hasBalance && isSettled && styles.balanceSettled,
          ]}
        >
          {hasBalance ? formatAmount(draft.balanceAmount ?? 0) : '—'}
        </Text>
        <Text style={styles.balanceLabel}>
          {hasBalance ? (isSettled ? 'Settled' : 'Outstanding') : 'Balance'}
        </Text>
      </View>
    </View>
  );
}

interface AddCustomerComposerProps {
  onClose: () => void;
  onSaved?: () => void;
  initialName?: string;
}

export default function AddCustomerComposer({
  onClose,
  onSaved,
  initialName,
}: AddCustomerComposerProps) {
  const db = useSQLiteContext();
  const { user } = useAuth();
  const { bumpData } = useShopData();
  const [draft, setDraft] = useState<CustomerDraft>(() => ({
    ...emptyCustomerDraft,
    name: initialName ?? '',
  }));
  const [isSaving, setIsSaving] = useState(false);
  const draftRef = useRef(draft);
  const persistCustomerRef = useRef<() => Promise<boolean>>(async () => false);

  useEffect(() => {
    draftRef.current = draft;
  }, [draft]);

  const applyResponse = useCallback((response: CustomerAgentActionResponse) => {
    if (isSaveCustomerAction(response)) {
      void persistCustomerRef.current();
      return { label: 'SAVE', updateContext: false };
    }

    const label = describeCustomerAction(response);
    const next = applyCustomerAction(draftRef.current, response);
    if (!next) {
      return null;
    }
    draftRef.current = next;
    setDraft(next);
    return { label };
  }, []);

  const {
    isSessionActive,
    heardText,
    commandStatus,
    errorMessage,
    modelsReady,
    downloadProgress,
    modelError,
    handleMicPress,
    endSession,
    clearAgentContext,
    showStatus,
  } = useVoiceAgent({
    schema: CustomerAgentActionResponseSchema,
    getSystemPrompt: () => CUSTOMER_SYSTEM_PROMPT_SHORT,
    applyResponse,
    isIncomplete: isIncompleteCustomerAction,
    isUnknown: isUnknownCustomerAction,
  });

  const handleCancel = () => {
    endSession();
    onClose();
  };

  const persistCustomer = useCallback(async (): Promise<boolean> => {
    if (!user) {
      showStatus('Unlock the app to save customers.', true);
      return false;
    }
    if (isSaving) {
      return false;
    }

    setIsSaving(true);
    const startedAt = Date.now();
    try {
      await insertCustomer(db, user.id, {
        name: draftRef.current.name,
        balanceAmount: draftRef.current.balanceAmount ?? 0,
      });
      bumpData();
      clearAgentContext();
      await waitForSaveFeedback(startedAt);
      endSession();
      onSaved?.();
      onClose();
      return true;
    } catch (error) {
      const message =
        error instanceof SaveRecordError || error instanceof DuplicateNameError
          ? error.message
          : 'Could not save the customer. Please try again.';
      showStatus(message, true);
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [bumpData, clearAgentContext, db, endSession, isSaving, onClose, onSaved, showStatus, user]);

  useEffect(() => {
    persistCustomerRef.current = persistCustomer;
  }, [persistCustomer]);

  const handleSave = () => {
    void persistCustomer();
  };

  return (
    <VoiceComposer
      title="New customer"
      subtitle="Speak a command — name and optional opening balance"
      onCancel={handleCancel}
      onSave={handleSave}
      isSaving={isSaving}
      heardText={heardText}
      commandStatus={commandStatus}
      errorMessage={errorMessage}
      modelError={modelError}
      modelsReady={modelsReady}
      downloadProgress={downloadProgress}
      isSessionActive={isSessionActive}
      onMicPress={handleMicPress}
    >
      <CustomerDraftCard draft={draft} />
    </VoiceComposer>
  );
}
