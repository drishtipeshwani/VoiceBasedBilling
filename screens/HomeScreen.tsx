import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import { useSQLiteContext } from 'expo-sqlite';
import InvoiceCard from '../components/InvoiceCard';
import AddCustomerComposer from '../components/AddCustomerComposer';
import AddStockComposer from '../components/AddStockComposer';
import SaveButton from '../components/SaveButton';
import { emptyInvoice } from '../data/emptyInvoice';
import { Invoice } from '../types/invoice';
import {
  AgentActionResponseSchema,
  type Action,
  type AgentActionResponse,
} from '../types/agentActionResponse';
import {
  SaveInvoiceError,
  customerExists,
  saveInvoice,
  stockItemExists,
} from '../db/queries';
import { buildInvoiceHtml } from '../utils/invoiceHtml';
import { useAuth } from '../utils/authContext';
import { useShopData } from '../utils/shopDataContext';
import {
  describeInvoiceAction,
  isIncompleteInvoiceAction,
  isSaveInvoiceAction,
  isUnknownInvoiceAction,
} from '../utils/applyInvoiceAction';
import {
  processGatedInvoiceActions,
  type EntityPrompt,
} from '../utils/invoiceEntityGate';
import { INVOICE_SYSTEM_PROMPT_SHORT } from '../utils/invoiceSystemPrompt';
import { waitForSaveFeedback } from '../utils/saveFeedback';
import { useVoiceAgent } from '../utils/useVoiceAgent';
import { styles } from './HomeScreen.styles';

export default function HomeScreen() {
  const { user, lock, unlocked } = useAuth();
  const db = useSQLiteContext();
  const { bumpData } = useShopData();

  const [invoice, setInvoice] = useState<Invoice>(() => ({
    ...emptyInvoice,
    companyName: user?.companyName ?? '',
  }));
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [activePrompt, setActivePrompt] = useState<EntityPrompt | null>(null);
  const [composerKind, setComposerKind] = useState<EntityPrompt['kind'] | null>(null);

  const invoiceRef = useRef(invoice);
  const activePromptRef = useRef<EntityPrompt | null>(null);
  const promptQueueRef = useRef<EntityPrompt[]>([]);
  const composerSavedRef = useRef(false);
  const persistInvoiceRef = useRef<() => Promise<boolean>>(async () => false);
  const resumeFromPromptRef = useRef<(applyPending: boolean) => void>(() => undefined);

  useEffect(() => {
    invoiceRef.current = invoice;
  }, [invoice]);

  useEffect(() => {
    activePromptRef.current = activePrompt;
  }, [activePrompt]);

  useEffect(() => {
    const companyName = user?.companyName ?? '';
    if (!companyName) return;
    setInvoice((current) =>
      current.companyName ? current : { ...current, companyName },
    );
  }, [user?.companyName]);

  const lookup = useCallback(
    () => ({
      customerExists: async (name: string) =>
        user ? customerExists(db, user.id, name) : false,
      stockItemExists: async (name: string) =>
        user ? stockItemExists(db, user.id, name) : false,
    }),
    [db, user],
  );

  const commitInvoice = useCallback((next: Invoice) => {
    invoiceRef.current = next;
    setInvoice(next);
  }, []);

  const showNextPrompt = useCallback((prompt: EntityPrompt | null) => {
    activePromptRef.current = prompt;
    setActivePrompt(prompt);
  }, []);

  const dequeueOrSetPrompt = useCallback(
    (prompt: EntityPrompt | null) => {
      if (prompt) {
        showNextPrompt(prompt);
        return;
      }
      const queued = promptQueueRef.current.shift() ?? null;
      showNextPrompt(queued);
    },
    [showNextPrompt],
  );

  const enqueuePrompt = useCallback(
    (prompt: EntityPrompt) => {
      if (activePromptRef.current) {
        promptQueueRef.current.push(prompt);
        return;
      }
      showNextPrompt(prompt);
    },
    [showNextPrompt],
  );

  const applyActionList = useCallback(
    async (actions: Action[]) => {
      if (actions.length === 0) {
        dequeueOrSetPrompt(null);
        return;
      }
      const outcome = await processGatedInvoiceActions(
        invoiceRef.current,
        actions,
        lookup(),
      );
      if (outcome.changed) {
        commitInvoice(outcome.invoice);
      }
      dequeueOrSetPrompt(outcome.prompt);
    },
    [commitInvoice, dequeueOrSetPrompt, lookup],
  );

  const resumeFromPrompt = useCallback(
    (applyPending: boolean) => {
      const prompt = activePromptRef.current;
      if (!prompt) {
        dequeueOrSetPrompt(null);
        return;
      }
      const remaining = applyPending
        ? [prompt.action, ...prompt.remaining]
        : prompt.remaining;
      void applyActionList(remaining);
    },
    [applyActionList, dequeueOrSetPrompt],
  );

  useEffect(() => {
    resumeFromPromptRef.current = resumeFromPrompt;
  }, [resumeFromPrompt]);

  const applyResponse = useCallback(
    async (formattedResponse: AgentActionResponse) => {
      if (isSaveInvoiceAction(formattedResponse)) {
        void persistInvoiceRef.current();
        return { label: 'SAVE_INVOICE', updateContext: false };
      }

      const outcome = await processGatedInvoiceActions(
        invoiceRef.current,
        formattedResponse,
        lookup(),
      );
      if (outcome.changed) {
        commitInvoice(outcome.invoice);
      }
      if (outcome.prompt) {
        enqueuePrompt(outcome.prompt);
      }
      if (!outcome.changed && !outcome.prompt) {
        return null;
      }
      const labeled = outcome.applied.length
        ? outcome.applied
        : outcome.prompt
          ? [outcome.prompt.action]
          : formattedResponse;
      return {
        label: describeInvoiceAction(labeled),
        updateContext: !outcome.prompt,
      };
    },
    [commitInvoice, enqueuePrompt, lookup],
  );

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
    schema: AgentActionResponseSchema,
    getSystemPrompt: () => INVOICE_SYSTEM_PROMPT_SHORT,
    applyResponse,
    isIncomplete: isIncompleteInvoiceAction,
    isUnknown: isUnknownInvoiceAction,
  });

  useEffect(() => {
    if (!unlocked) {
      endSession();
    }
  }, [unlocked, endSession]);

  const handleLock = () => {
    endSession();
    lock();
  };

  const persistInvoice = useCallback(async (): Promise<boolean> => {
    if (!user) {
      showStatus('Unlock the app to save invoices.', true);
      return false;
    }
    if (isSaving) {
      return false;
    }

    setIsSaving(true);
    const startedAt = Date.now();
    try {
      await saveInvoice(db, user.id, invoiceRef.current);
      await waitForSaveFeedback(startedAt);
      clearAgentContext();
      promptQueueRef.current = [];
      showNextPrompt(null);
      setComposerKind(null);
      setInvoice({
        ...emptyInvoice,
        companyName: user.companyName,
      });
      bumpData();
      showStatus('Invoice saved', false);
      return true;
    } catch (error) {
      const message =
        error instanceof SaveInvoiceError
          ? error.message
          : 'Could not save the invoice. Please try again.';
      showStatus(message, true);
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [bumpData, clearAgentContext, db, isSaving, showNextPrompt, showStatus, user]);

  useEffect(() => {
    persistInvoiceRef.current = persistInvoice;
  }, [persistInvoice]);

  const handleSaveInvoice = () => {
    void persistInvoice();
  };

  const handlePromptNo = () => {
    resumeFromPrompt(false);
  };

  const handlePromptYes = () => {
    if (!activePromptRef.current) {
      return;
    }
    endSession();
    composerSavedRef.current = false;
    setComposerKind(activePromptRef.current.kind);
  };

  const handleComposerSaved = () => {
    composerSavedRef.current = true;
  };

  const handleComposerClose = () => {
    const saved = composerSavedRef.current;
    composerSavedRef.current = false;
    setComposerKind(null);
    resumeFromPromptRef.current(saved);
  };

  const handleDownloadPdf = async () => {
    setPdfError(null);
    setIsGeneratingPdf(true);
    try {
      const html = buildInvoiceHtml(invoice);
      const { uri } = await Print.printToFileAsync({ html });

      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, {
          UTI: '.pdf',
          mimeType: 'application/pdf',
        });
      } else {
        setPdfError('Sharing is not available on this device.');
      }
    } catch {
      setPdfError('Could not generate the PDF. Please try again.');
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  const statusText = !modelsReady
    ? `Loading LLM… ${Math.round(downloadProgress * 100)}%`
    : isSessionActive
      ? 'Listening…'
      : 'Tap to speak a command';

  if (composerKind === 'customer' && activePrompt) {
    return (
      <AddCustomerComposer
        initialName={activePrompt.name}
        onSaved={handleComposerSaved}
        onClose={handleComposerClose}
      />
    );
  }

  if (composerKind === 'stock' && activePrompt) {
    return (
      <AddStockComposer
        initialName={activePrompt.name}
        onSaved={handleComposerSaved}
        onClose={handleComposerClose}
      />
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>Voice Invoice</Text>
          <Text style={styles.subtitle}>
            Speak a command — on-device speech recognition + LLM
          </Text>
        </View>
        <View style={styles.headerActions}>
          <Pressable
            onPress={handleLock}
            style={({ pressed }) => [
              styles.signOutButton,
              pressed && styles.signOutButtonPressed,
            ]}
          >
            <Text style={styles.signOutText}>Lock</Text>
          </Pressable>
          <View style={styles.actionButtonsRow}>
            <SaveButton onPress={handleSaveInvoice} isSaving={isSaving} />
            <Pressable
              onPress={handleDownloadPdf}
              disabled={isGeneratingPdf}
              style={({ pressed }) => [
                styles.downloadButton,
                pressed && styles.downloadButtonPressed,
              ]}
            >
              {isGeneratingPdf ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <Text style={styles.downloadButtonText}>PDF ⬇</Text>
              )}
            </Pressable>
          </View>
        </View>
      </View>

      {heardText ? (
        <Text style={styles.heardText} numberOfLines={2}>
          Heard: {heardText}
        </Text>
      ) : null}

      {commandStatus ? (
        <Text
          style={[
            styles.commandStatusText,
            commandStatus.isError && styles.commandStatusTextError,
          ]}
          numberOfLines={2}
        >
          {commandStatus.message}
        </Text>
      ) : null}

      {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
      {modelError ? <Text style={styles.errorText}>{modelError}</Text> : null}
      {pdfError ? <Text style={styles.errorText}>{pdfError}</Text> : null}

      {activePrompt ? (
        <View style={styles.promptBanner}>
          <Text style={styles.promptText}>
            {activePrompt.kind === 'customer'
              ? `Customer ${activePrompt.name} is not in the ledger. Create them?`
              : `Item ${activePrompt.name} is not in inventory. Create it?`}
          </Text>
          <View style={styles.promptActions}>
            <Pressable
              onPress={handlePromptYes}
              accessibilityLabel="Create missing record"
              style={({ pressed }) => [styles.promptYes, pressed && styles.promptButtonPressed]}
            >
              <Text style={styles.promptYesText}>Yes</Text>
            </Pressable>
            <Pressable
              onPress={handlePromptNo}
              accessibilityLabel="Skip creating missing record"
              style={({ pressed }) => [styles.promptNo, pressed && styles.promptButtonPressed]}
            >
              <Text style={styles.promptNoText}>No</Text>
            </Pressable>
          </View>
        </View>
      ) : null}

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <InvoiceCard invoice={invoice} />
      </ScrollView>

      <View style={styles.footer}>
        <Text style={styles.statusText}>{statusText}</Text>
        <Pressable
          onPress={handleMicPress}
          disabled={!modelsReady && !isSessionActive}
          style={({ pressed }) => [
            styles.micButton,
            isSessionActive && styles.micButtonActive,
            !modelsReady && !isSessionActive && styles.micButtonDisabled,
            pressed && styles.micButtonPressed,
          ]}
        >
          {!modelsReady && !isSessionActive ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.micIcon}>{isSessionActive ? '⏹' : '🎤'}</Text>
          )}
        </Pressable>
      </View>
    </SafeAreaView>
  );
}
