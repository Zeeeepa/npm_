import type { NpmSearchResult, NpmPackage, FileNode, EnrichedNpmPackage, NpmPackageVersion } from '../types';

const NPM_REGISTRY_API = 'https://registry.npmjs.org';
const NPM_SEARCH_API = `${NPM_REGISTRY_API}/-/v1/search`;
const UNPKG_API = 'https://unpkg.com';

const NPM_SEARCH_API_LIMIT = 10000;

export class NpmApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = 'NpmApiError';
  }
}

export class NetworkError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'NetworkError';
    }
}

async function handleResponse(response: Response) {
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Failed to read error response.');
    throw new NpmApiError(`NPM API error: ${response.statusText} (${response.status}) - ${errorText}`, response.status);
  }
  return response.json();
}

async function fetchWithRetry(url: string, options: RequestInit, retries = 3, initialDelay = 500): Promise<Response> {
    let delay = initialDelay;
    for (let i = 0; i < retries; i++) {
        if (options.signal?.aborted) {
            const abortError = new DOMException('The user aborted a request.', 'AbortError');
            throw abortError;
        }
        try {
            const response = await fetch(url, options);
            // Only retry on 5xx server errors. 4xx are client errors and won't be fixed by retrying.
            if (response.status >= 500 && i < retries - 1) {
                console.warn(`Server error (${response.status}). Retrying in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                delay *= 2;
                continue; // retry
            }
            return response; // Success or non-retryable error (e.g., 404)
        } catch (error) {
             if (error.name === 'AbortError') {
                throw error; // Propagate abort error immediately
            }
            
            if (i === retries - 1) { // This was the last attempt
                console.error(`Request failed after ${retries} attempts.`, error);
                throw new NetworkError('Could not connect to the NPM registry. Please check your internet connection and try again.');
            }

            console.warn(`Network error on attempt ${i + 1}. Retrying in ${delay}ms...`, error);
            await new Promise(resolve => setTimeout(resolve, delay));
            delay *= 2; // Exponential backoff
        }
    }
    // This line should be unreachable if retries > 0
    throw new NetworkError('Request failed after all retries.');
}


export async function searchNpm(
    query: string, 
    weights: { quality: number, popularity: number, maintenance: number },
    isWeightingEnabled: boolean,
    from: number = 0, 
    size: number = 250,
    signal?: AbortSignal
): Promise<{ objects: NpmSearchResult[], total: number }> {
    if (!query.trim()) {
        return { objects: [], total: 0 };
    }

    const params = new URLSearchParams({
        text: query,
        size: size.toString(),
        from: from.toString(),
    });

    if (isWeightingEnabled) {
        params.append('quality', weights.quality.toFixed(1));
        params.append('popularity', weights.popularity.toFixed(1));
        params.append('maintenance', weights.maintenance.toFixed(1));
    }

    const url = `${NPM_SEARCH_API}?${params.toString()}`;

    const response = await fetchWithRetry(url, { signal });
    return handleResponse(response);
}

const DEEP_SEARCH_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789'.split('');

export async function* deepSearchNpm(
    query: string,
    weights: { quality: number; popularity: number; maintenance: number },
    isWeightingEnabled: boolean,
    signal?: AbortSignal
): AsyncGenerator<{ packages: NpmSearchResult[]; totalFound: number; progress: number }> {
    const seenPackages = new Set<string>();

    // Step 1: Perform initial search to get a baseline and total estimate
    const initialData = await searchNpm(query, weights, isWeightingEnabled, 0, 250, signal);
    const totalEstimate = initialData.total;
    
    // Step 2: Fetch all results from the initial query (up to 10,000)
    let currentFrom = 0;
    while (currentFrom < NPM_SEARCH_API_LIMIT) {
        if (signal?.aborted) return;
        const pageData = await searchNpm(query, weights, isWeightingEnabled, currentFrom, 250, signal);
        
        const newPackages = pageData.objects.filter(p => !seenPackages.has(p.package.name));
        if (newPackages.length > 0) {
            newPackages.forEach(p => seenPackages.add(p.package.name));
            yield { packages: newPackages, totalFound: seenPackages.size, progress: 0 };
        }

        currentFrom += pageData.objects.length;
        if (pageData.objects.length < 250) break; // Reached the end of results for this query
    }

    // Step 3: If total estimate is over the limit, start deep search with sub-queries
    if (totalEstimate <= seenPackages.size) {
        return; // We got everything in the initial search
    }

    for (let i = 0; i < DEEP_SEARCH_CHARS.length; i++) {
        if (signal?.aborted) return;
        
        const char = DEEP_SEARCH_CHARS[i];
        const subQuery = `${query} ${char}`;
        currentFrom = 0;
        const progress = ((i + 1) / DEEP_SEARCH_CHARS.length) * 100;

        while (currentFrom < NPM_SEARCH_API_LIMIT) {
            if (signal?.aborted) return;
            try {
                const pageData = await searchNpm(subQuery, weights, isWeightingEnabled, currentFrom, 250, signal);
                
                const newPackages = pageData.objects.filter(p => !seenPackages.has(p.package.name));
                if (newPackages.length > 0) {
                    newPackages.forEach(p => seenPackages.add(p.package.name));
                    yield { packages: newPackages, totalFound: seenPackages.size, progress };
                }
               
                currentFrom += pageData.objects.length;
                if (pageData.objects.length < 250) break; // End of this sub-query's results
            } catch (e) {
                if (e.name !== 'AbortError') {
                    console.error(`Error in sub-query "${subQuery}"`, e);
                }
                break; // Move to next sub-query on error
            }
        }
    }
}


export async function getPackageInfo(packageName: string, signal?: AbortSignal): Promise<NpmPackage> {
  const url = `${NPM_REGISTRY_API}/${encodeURIComponent(packageName)}`;
  const response = await fetchWithRetry(url, { signal });
  return handleResponse(response);
}

export async function getPackageVersionDetails(packageName: string, signal?: AbortSignal): Promise<NpmPackageVersion | null> {
    try {
        const pkg = await getPackageInfo(packageName, signal);
        const latestVersionTag = pkg['dist-tags']?.latest;
        if (latestVersionTag && pkg.versions?.[latestVersionTag]) {
            return pkg.versions[latestVersionTag];
        }
        return null;
    } catch (e) {
        if (e.name !== 'AbortError') {
          console.error(`Failed to fetch details for ${packageName}`, e);
        }
        return null;
    }
}

export async function getPackageFileTree(packageName: string, version: string, signal?: AbortSignal): Promise<FileNode> {
  const url = `${UNPKG_API}/${encodeURIComponent(packageName)}@${version}/?meta`;
  const response = await fetchWithRetry(url, { signal });
  const data = await handleResponse(response);
  return data;
}

export async function getFileContent(packageName: string, version: string, path: string, signal?: AbortSignal): Promise<string> {
    const url = `${UNPKG_API}/${encodeURIComponent(packageName)}@${version}${path}`;
    const response = await fetchWithRetry(url, { signal });
     if (!response.ok) {
        throw new NpmApiError(`Failed to fetch file content from unpkg: ${response.statusText}`, response.status);
    }
    return response.text();
}