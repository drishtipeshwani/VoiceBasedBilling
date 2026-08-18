const MIN_SAVE_FEEDBACK_MS = 700;

export function waitForSaveFeedback(startedAt: number): Promise<void> {
  const remaining = MIN_SAVE_FEEDBACK_MS - (Date.now() - startedAt);
  if (remaining <= 0) {
    return Promise.resolve();
  }
  return new Promise((resolve) => setTimeout(resolve, remaining));
}
