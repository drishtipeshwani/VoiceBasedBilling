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
import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
} from 'expo-speech-recognition';
import {
  fixAndValidateStructuredOutput,
} from 'react-native-executorch';
import InvoiceCard from '../components/InvoiceCard';
import { emptyInvoice } from '../data/emptyInvoice';
import { Invoice } from '../types/invoice';
import {
  AgentResponseSchema,
  type AgentResponse,
} from '../types/agentResponse';
import { buildInvoiceHtml } from '../utils/invoiceHtml';
import { useAuth } from '../utils/authContext';
import { useOnDeviceAI } from '../utils/OnDeviceAIProvider';
import {
  applyAgentResponse,
  describeAgentResponse,
} from '../utils/applyInvoiceAction';
import {
  INVOICE_SYSTEM_PROMPT,
  INVOICE_SYSTEM_PROMPT_SHORT,
} from '../utils/invoiceLlm';
import { usesFinetunedInvoiceLlm } from '../utils/invoiceModel';
import { styles } from './HomeScreen.styles';

const MAX_SESSION_DURATION_MS = 60000;
const COMMAND_STATUS_DISPLAY_MS = 2500;

interface CommandStatus {
  message: string;
  isError: boolean;
}

export default function HomeScreen() {
  const { signOut } = useAuth();
  const { llm } = useOnDeviceAI();

  const [invoice, setInvoice] = useState<Invoice>(emptyInvoice);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [heardText, setHeardText] = useState('');
  const [commandStatus, setCommandStatus] = useState<CommandStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const sessionActiveRef = useRef(false);
  const committedTextRef = useRef('');
  const invoiceRef = useRef(invoice);
  const safetyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const commandStatusTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const llmRef = useRef(llm);
  const utteranceQueueRef = useRef<string[]>([]);
  const isProcessingQueueRef = useRef(false);
  const lastSuccessfulAgentResponseRef = useRef<AgentResponse | null>(null);

  useEffect(() => {
    llmRef.current = llm;
  }, [llm]);

  useEffect(() => {
    if (!llm.isReady) {
      return;
    }
    llm.configure({
      generationConfig: {
        temperature: 0,
      },
    });
  }, [llm.isReady, llm.configure]);

  useEffect(() => {
    invoiceRef.current = invoice;
  }, [invoice]);

  const modelsReady = llm.isReady;
  const downloadProgress = llm.downloadProgress;
  const modelError = llm.error?.message ?? null;

  const clearSafetyTimer = useCallback(() => {
    if (safetyTimerRef.current) {
      clearTimeout(safetyTimerRef.current);
      safetyTimerRef.current = null;
    }
  }, []);

  const clearTranscript = useCallback(() => {
    committedTextRef.current = '';
    setHeardText('');
  }, []);

  const clearUtteranceQueue = useCallback(() => {
    utteranceQueueRef.current = [];
  }, []);

  const clearAgentContext = useCallback(() => {
    lastSuccessfulAgentResponseRef.current = null;
  }, []);

  const scheduleCommandStatusClear = useCallback(() => {
    if (commandStatusTimerRef.current) {
      clearTimeout(commandStatusTimerRef.current);
    }
    commandStatusTimerRef.current = setTimeout(() => {
      setCommandStatus(null);
    }, COMMAND_STATUS_DISPLAY_MS);
  }, []);

  const processUtterance = useCallback(
    async (input: string) => {
      const currentLlm = llmRef.current;
      if (!currentLlm.isReady) {
        return;
      }

      console.log('[HomeScreen] Agent input:', input);

      try {
        setCommandStatus({ message: 'Running on-device LLM…', isError: false });

        const lastAgentResponse = lastSuccessfulAgentResponseRef.current;
        const systemPrompt = usesFinetunedInvoiceLlm
          ? INVOICE_SYSTEM_PROMPT_SHORT
          : INVOICE_SYSTEM_PROMPT;
        const reply = await currentLlm.generate([
          { role: 'system' as const, content: systemPrompt },
          ...(lastAgentResponse
            ? [
                {
                  role: 'assistant' as const,
                  content: JSON.stringify(lastAgentResponse),
                },
              ]
            : []),
          { role: 'user' as const, content: input },
        ]);

        console.log('[HomeScreen] Agent raw output:', reply);
        const formattedResponse = fixAndValidateStructuredOutput(
          reply,
          AgentResponseSchema,
        );
        console.log('[HomeScreen] Parsed agent response:', JSON.stringify(formattedResponse));

        if (!formattedResponse) {
          setCommandStatus({
            message: 'Could not parse LLM response',
            isError: true,
          });
          scheduleCommandStatusClear();
          return;
        }

        if (formattedResponse.incompleteInput) {
          setCommandStatus({
            message: 'Waiting for a complete command',
            isError: false,
          });
          scheduleCommandStatusClear();
          return;
        }

        if (formattedResponse.unknownInput) {
          setCommandStatus({ message: 'Unknown command', isError: true });
          scheduleCommandStatusClear();
          return;
        }

        const label = describeAgentResponse(formattedResponse);
        const next = applyAgentResponse(invoiceRef.current, formattedResponse);
        if (!next) {
          setCommandStatus({
            message: `Could not apply ${label}`,
            isError: true,
          });
          scheduleCommandStatusClear();
          return;
        }

        invoiceRef.current = next;
        lastSuccessfulAgentResponseRef.current = formattedResponse;
        setInvoice(next);
        setCommandStatus({
          message: `Applied: ${label}`,
          isError: false,
        });
        scheduleCommandStatusClear();
      } catch (error) {
        console.error('[HomeScreen] LLM generate failed:', error);
        setCommandStatus({
          message: 'LLM inference failed',
          isError: true,
        });
        scheduleCommandStatusClear();
      }
    },
    [scheduleCommandStatusClear],
  );

  const processQueue = useCallback(async () => {
    if (isProcessingQueueRef.current) {
      return;
    }

    isProcessingQueueRef.current = true;
    try {
      while (utteranceQueueRef.current.length > 0) {
        const next = utteranceQueueRef.current.shift();
        if (!next) {
          continue;
        }
        await processUtterance(next);
      }
    } finally {
      isProcessingQueueRef.current = false;
      if (utteranceQueueRef.current.length > 0) {
        void processQueue();
      }
    }
  }, [processUtterance]);

  const enqueueUtterance = useCallback(
    (committedSegment: string) => {
      const input = committedSegment.trim();
      if (!input) {
        return;
      }
      if (!llmRef.current.isReady) {
        return;
      }

      utteranceQueueRef.current.push(input);

      if (isProcessingQueueRef.current) {
        const pending = utteranceQueueRef.current.length;
        setCommandStatus({
          message: `Queued (${pending} waiting)…`,
          isError: false,
        });
      }

      void processQueue();
    },
    [processQueue],
  );

  const enqueueUtteranceRef = useRef(enqueueUtterance);
  useEffect(() => {
    enqueueUtteranceRef.current = enqueueUtterance;
  }, [enqueueUtterance]);

  const endSession = useCallback(() => {
    if (!sessionActiveRef.current) {
      return;
    }
    sessionActiveRef.current = false;
    setIsSessionActive(false);
    clearSafetyTimer();
    ExpoSpeechRecognitionModule.stop();
  }, [clearSafetyTimer]);

  const scheduleSafetyCap = useCallback(() => {
    clearSafetyTimer();
    safetyTimerRef.current = setTimeout(endSession, MAX_SESSION_DURATION_MS);
  }, [clearSafetyTimer, endSession]);

  useSpeechRecognitionEvent('result', (event) => {
    if (!sessionActiveRef.current) return;

    const transcript = event.results[0]?.transcript ?? '';

    if (event.isFinal) {
      committedTextRef.current += transcript + ' ';
      setHeardText(committedTextRef.current.trim());
      enqueueUtteranceRef.current(transcript);
    } else {
      setHeardText((committedTextRef.current + transcript).trim());
    }
  });

  useSpeechRecognitionEvent('error', (event) => {
    console.error('[HomeScreen] Speech recognition error:', event.error, event.message);
    if (sessionActiveRef.current) {
      endSession();
      setErrorMessage(`Speech recognition failed: ${event.message}`);
    }
  });

  useSpeechRecognitionEvent('end', () => {
    if (sessionActiveRef.current) {
      endSession();
    }
  });

  useEffect(() => {
    return () => {
      clearSafetyTimer();
      clearUtteranceQueue();
      if (commandStatusTimerRef.current) {
        clearTimeout(commandStatusTimerRef.current);
      }
      if (sessionActiveRef.current) {
        sessionActiveRef.current = false;
        ExpoSpeechRecognitionModule.stop();
      }
    };
  }, [clearSafetyTimer, clearUtteranceQueue]);

  const startSession = useCallback(async () => {
    if (!modelsReady) {
      setErrorMessage('On-device LLM is still loading. Please wait.');
      return;
    }

    const { granted } =
      await ExpoSpeechRecognitionModule.requestPermissionsAsync();
    if (!granted) {
      setErrorMessage('Microphone and speech recognition permissions are required.');
      return;
    }

    clearTranscript();
    clearUtteranceQueue();
    clearAgentContext();
    setErrorMessage(null);
    setCommandStatus(null);

    sessionActiveRef.current = true;
    setIsSessionActive(true);
    scheduleSafetyCap();

    ExpoSpeechRecognitionModule.start({
      lang: 'en-IN',
      interimResults: true,
      continuous: true,
      requiresOnDeviceRecognition: true,
      addsPunctuation: false,
    });
  }, [
    modelsReady,
    clearTranscript,
    clearUtteranceQueue,
    clearAgentContext,
    scheduleSafetyCap,
  ]);

  const handleMicPress = () => {
    if (isSessionActive) {
      endSession();
    } else {
      void startSession();
    }
  };

  const handleSignOut = () => {
    endSession();
    signOut();
  };

  const handleSaveInvoice = () => {
    // The next invoice must not inherit this one's item, or an ellipsis like
    // "make its price 20" would attach to an item that is no longer on screen.
    clearAgentContext();
    setCommandStatus({ message: 'Invoice saved (demo)', isError: false });
    scheduleCommandStatusClear();
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
            onPress={handleSignOut}
            style={({ pressed }) => [
              styles.signOutButton,
              pressed && styles.signOutButtonPressed,
            ]}
          >
            <Text style={styles.signOutText}>Sign out</Text>
          </Pressable>
          <View style={styles.actionButtonsRow}>
            <Pressable
              onPress={handleSaveInvoice}
              style={({ pressed }) => [
                styles.saveButton,
                pressed && styles.saveButtonPressed,
              ]}
            >
              <Text style={styles.saveButtonText}>Save</Text>
            </Pressable>
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
