// types.ts

export interface NpmSearchOptions {
  text: string;
  popularity?: number;
  quality?: number;
  maintenance?: number;
  size?: number;
}

export interface NpmSearchResult {
  package: {
    name: string;
    scope: string;
    version: string;
    description: string;
    keywords?: string[];
    date: string;
    links: {
      npm: string;
      homepage?: string;
      repository?: string;
      bugs?: string;
    };
    author?: {
      name: string;
      email?: string;
      url?: string;
    };
    publisher: {
      username: string;
      email: string;
    };
    maintainers: {
      username: string;
      email: string;
    }[];
  };
  score: {
    final: number;
    detail: {
      quality: number;
      popularity: number;
      maintenance: number;
    };
  };
  searchScore: number;
}

export interface NpmPackage {
  name: string;
  description: string;
  'dist-tags': {
    latest: string;
    [key: string]: string;
  };
  versions: {
    [version: string]: NpmPackageVersion;
  };
  time: {
    created: string;
    modified: string;
    [version: string]: string;
  };
  maintainers: { name: string; email: string }[];
  homepage: string;
  keywords: string[];
  repository: {
    type: string;
    url: string;
  };
  author: {
    name: string;
  };
  bugs: {
    url: string;
  };
  license: string;
  readme: string;
  readmeFilename: string;
}

export interface NpmPackageVersion {
  name: string;
  version: string;
  description: string;
  main: string;
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
  peerDependencies?: Record<string, string>;
  repository: {
    type: string;
    url: string;
  };
  dist: {
    shasum: string;
    tarball: string;
    fileCount: number;
    unpackedSize: number;
  };
}

export interface FileNode {
  path: string;
  type: 'file' | 'directory';
  files?: FileNode[];
  size?: number;
}

export type SyncStatus = 'synced' | 'not_synced' | 'syncing';

export type SupabaseStatus = 'disconnected' | 'connected' | 'error' | 'initializing' | 'connecting';

export interface EnrichedNpmPackage extends NpmSearchResult {
    details?: NpmPackageVersion;
    syncStatus?: SyncStatus;
    supabaseStatus?: SupabaseStatus;
}

export interface PastSearch {
  id: string; // Composite key of query and timestamp
  timestamp: number;
  query: string;
  results: EnrichedNpmPackage[];
  totalFound: number;
  searchMode: string;
  weights: { quality: number; popularity: number; maintenance: number };
  filtersEnabled: { weighting: boolean };
}

export interface FlatFile {
  path: string;
  size?: number;
}

// FIX: Add ProjectRepository interface for GitHub repository data.
export interface ProjectRepository {
  full_name: string;
  description: string | null;
  language: string | null;
}

export interface SupabaseCredentials {
  url: string;
  key: string; // Anon key
  secretKey?: string; // Service Role key
}