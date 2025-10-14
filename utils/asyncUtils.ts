// utils/asyncUtils.ts

/**
 * Processes an array of items with a limited number of concurrent async operations.
 * @param items The array of items to process.
 * @param processor A function that takes an item and returns a Promise.
 * @param concurrency The maximum number of promises to run in parallel.
 * @param onResult A callback function that is called with the result of each successful promise.
 * @param onError A callback function that is called when a processor promise rejects.
 * @param signal An AbortSignal to cancel ongoing operations.
 */
export async function processWithConcurrency<T, R>({
  items,
  processor,
  concurrency,
  onResult,
  onError,
  signal,
}: {
  items: T[];
  processor: (item: T, signal: AbortSignal) => Promise<R | null>;
  concurrency: number;
  onResult: (item: T, result: R) => void;
  onError?: (item: T, error: Error) => void;
  signal: AbortSignal;
}): Promise<void> {
  const queue = [...items];
  const activePromises: Promise<void>[] = [];

  const run = async (): Promise<void> => {
    while (queue.length > 0) {
      if (signal.aborted) {
        return;
      }

      const item = queue.shift()!;
      
      const promise = processor(item, signal)
        .then(result => {
          if (result && !signal.aborted) {
            onResult(item, result);
          }
        })
        .catch(err => {
          if (err.name !== 'AbortError') {
            // Log error but don't stop the pool
            console.error(`Error processing item:`, item, err);
            if (onError) {
              onError(item, err);
            }
          }
        });
        
      const wrappedPromise = promise.finally(() => {
        // Remove this promise from the active list
        const index = activePromises.indexOf(wrappedPromise);
        if (index > -1) {
          activePromises.splice(index, 1);
        }
      });
      
      activePromises.push(wrappedPromise);
      
      if (activePromises.length >= concurrency) {
        // Wait for any promise to finish
        await Promise.race(activePromises);
      }
    }
    // Wait for all remaining promises to finish
    await Promise.all(activePromises);
  };
  
  await run();
}