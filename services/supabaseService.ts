import { createClient, SupabaseClient, PostgrestError } from '@supabase/supabase-js';
import { getPackageInfo, getPackageFileTree } from './searchService';
import type { FileNode } from '../types';


// ============================================================================
// TYPES
// ============================================================================

export interface Package {
  id?: number;
  name: string;
  package_data: any;
  description?: string;
  repository_url?: string;
  homepage_url?: string;
  npm_url?: string;
  author?: any;
  maintainers?: any;
  keywords?: string[];
  license?: string;
  created_at?: string;
  updated_at?: string;
  last_synced_at?: string;
  download_stats?: any;
  github_stars?: number;
  github_forks?: number;
  github_issues?: number;
  npm_version_count?: number;
  is_deprecated?: boolean;
  deprecation_message?: string;
}

export interface PackageVersion {
  id?: number;
  package_name: string;
  version: string;
  version_major?: number;
  version_minor?: number;
  version_patch?: number;
  is_latest?: boolean;
  is_prerelease?: boolean;
  tarball_url?: string;
  shasum?: string;
  integrity?: string;
  unpacked_size?: number;
  file_count?: number;
  dependencies?: any;
  dev_dependencies?: any;
  peer_dependencies?: any;
  optional_dependencies?: any;
  bundled_dependencies?: any;
  published_at?: string;
  published_by?: any;
  git_head?: string;
  node_version?: string;
  npm_version?: string;
  scripts?: any;
  bin?: any;
  main_entry_point?: string;
  module_entry_point?: string;
  types_entry_point?: string;
  exports?: any;
  contents_synced?: boolean;
  synced_at?: string;
  created_at?: string;
}

export interface PackageAnalysis {
  id?: string;
  package_name: string;
  analyzed_at?: string;
  analysis_version?: string;
  total_files?: number;
  total_lines_of_code?: number;
  total_size_bytes?: number;
  language_breakdown?: any;
  average_complexity?: number;
  max_complexity?: number;
  total_functions?: number;
  total_classes?: number;
  total_interfaces?: number;
  direct_dependencies?: number;
  dev_dependencies?: number;
  peer_dependencies?: number;
  total_dependencies?: number;
  maintainability_score?: number;
  test_coverage?: number;
  documentation_coverage?: number;
  known_vulnerabilities?: number;
  license_issues?: any;
  has_tests?: boolean;
  has_typescript?: boolean;
  has_documentation?: boolean;
  build_tools?: any;
  frameworks?: any;
  analysis_metadata?: any;
}

export interface DirectoryEntry {
  id?: string;
  version_id: number;
  path: string;
  name: string;
  type: 'file' | 'directory' | 'symlink';
  parent_path?: string;
  depth?: number;
  size_bytes?: number;
  mode?: string;
  created_at?: string;
}

export interface CodeFile {
  id?: string;
  version_id: number;
  directory_entry_id?: string;
  path: string;
  storage_path?: string;
  content?: string;
  content_hash?: string;
  encoding?: string;
  language?: string;
  file_type?: string;
  file_extension?: string;
  mime_type?: string;
  is_binary?: boolean;
  is_generated?: boolean;
  is_minified?: boolean;
  is_test_file?: boolean;
  is_entry_point?: boolean;
  line_count?: number;
  char_count?: number;
  blank_lines?: number;
  comment_lines?: number;
  code_lines?: number;
  size_bytes?: number;
  imports?: any;
  exports?: any;
  requires?: any;
  external_dependencies?: string[];
  parsed?: boolean;
  parse_error?: string;
  ast_hash?: string;
  file_metadata?: any;
  created_at?: string;
}

export interface CodeSymbol {
  id?: string;
  file_id: string;
  version_id: number;
  parent_symbol_id?: string;
  name: string;
  qualified_name?: string;
  display_name?: string;
  symbol_type: string;
  symbol_kind?: string;
  scope?: string;
  visibility?: string;
  is_exported?: boolean;
  export_type?: string;
  is_static?: boolean;
  is_abstract?: boolean;
  is_async?: boolean;
  is_generator?: boolean;
  is_readonly?: boolean;
  is_optional?: boolean;
  start_line?: number;
  end_line?: number;
  start_col?: number;
  end_col?: number;
  signature?: string;
  parameters?: any;
  return_type?: string;
  type_parameters?: any;
  extends_types?: string[];
  implements_types?: string[];
  value_type?: string;
  initial_value?: string;
  docstring?: string;
  doc_tags?: any;
  description?: string;
  decorators?: any;
  modifiers?: string[];
  complexity_score?: number;
  lines_of_code?: number;
  cognitive_complexity?: number;
  inferred_type?: string;
  type_complexity?: number;
  is_used?: boolean;
  usage_count?: number;
  symbol_metadata?: any;
  created_at?: string;
}

export interface FileDependency {
  id?: string;
  version_id: number;
  source_file_id: string;
  target_file_id?: string;
  source_path: string;
  import_statement: string;
  resolved_path?: string;
  dependency_type: string;
  import_kind?: string;
  imported_symbols?: any;
  is_wildcard?: boolean;
  is_default?: boolean;
  is_side_effect?: boolean;
  is_external?: boolean;
  package_name?: string;
  package_version?: string;
  is_dev_dependency?: boolean;
  is_peer_dependency?: boolean;
  line_number?: number;
  column_number?: number;
  created_at?: string;
}

export interface CodeReference {
  id?: string;
  version_id: number;
  symbol_id: string;
  file_id: string;
  line_number: number;
  column_number: number;
  end_line?: number;
  end_column?: number;
  reference_type: string;
  context?: string;
  is_constructor_call?: boolean;
  arguments?: any;
  created_at?: string;
}

export interface PastSearch {
  id: string;
  created_at?: string;
  query: string;
  search_mode: string;
  total_found: number;
  search_duration_ms?: number;
  filters: any;
  sort_by?: string;
  results_data: any;
  result_count?: number;
  user_clicked?: boolean;
  clicked_package_name?: string;
  time_to_click_ms?: number;
}

export interface SearchResultItem {
  id?: string;
  search_id: string;
  package_name: string;
  result_position: number;
  relevance_score?: number;
  package_snapshot?: any;
  created_at?: string;
}

export interface SavedPackage {
  id?: number;
  package_name: string;
  saved_at?: string;
  notes?: string;
  tags?: string[];
  favorite?: boolean;
}

// ============================================================================
// CLIENT INITIALIZATION
// ============================================================================

let supabaseInstance: SupabaseClient | null = null;
let projectRef: string | null = null;

const getSupabase = (): SupabaseClient => {
  if (!supabaseInstance) {
    throw new Error("Supabase client has not been initialized. Please call 'init' first.");
  }
  return supabaseInstance;
};

export const getProjectRef = (): string | null => {
  return projectRef;
};

export const init = (url: string, anonKey: string, serviceKey?: string) => {
  if (!url || !anonKey) throw new Error('Supabase URL and Anon Key are required.');
  
  try {
    const urlObject = new URL(url);
    projectRef = urlObject.hostname.split('.')[0];
  } catch(e) {
    console.error("Could not parse project ref from Supabase URL:", url);
    projectRef = null;
  }

  const options = serviceKey ? {
    global: { headers: { Authorization: `Bearer ${serviceKey}` } },
  } : {};

  supabaseInstance = createClient(url, anonKey, options);
};

export const verifySchema = async (): Promise<{ success: boolean; missing: string[]; error?: Error | null }> => {
  const requiredTables = [
    'packages',
    'package_versions',
    'package_analyses',
    'directory_tree',
    'code_files',
    'code_symbols',
    'file_dependencies',
    'code_references',
    'saved_packages',
    'past_searches',
    'search_result_items'
  ];
  const missingTables: string[] = [];

  for (const table of requiredTables) {
    const { error } = await getSupabase().from(table).select('*', { count: 'exact', head: true }).limit(1);
    if (error) {
      const pgError = error as PostgrestError;
      if (pgError.code === '42P01' || pgError.message.includes("does not exist")) {
        missingTables.push(table);
      } else {
        return { success: false, missing: requiredTables, error: pgError };
      }
    }
  }

  return {
    success: missingTables.length === 0,
    missing: missingTables,
    error: null,
  };
};

// ============================================================================
// PACKAGES API
// ============================================================================

export const packages = {
  // Get all packages with optional filters
  getAll: async (options?: {
    limit?: number;
    offset?: number;
    orderBy?: string;
    ascending?: boolean;
    savedOnly?: boolean;
    deprecated?: boolean;
  }): Promise<Package[]> => {
    let query = getSupabase().from('packages').select('*');
    
    if (options?.savedOnly) {
      const { data: saved } = await getSupabase()
        .from('saved_packages')
        .select('package_name');
      if (saved && saved.length > 0) {
        query = query.in('name', saved.map(s => s.package_name));
      } else {
        return [];
      }
    }
    
    if (options?.deprecated !== undefined) {
      query = query.eq('is_deprecated', options.deprecated);
    }
    
    if (options?.orderBy) {
      query = query.order(options.orderBy, { ascending: options.ascending ?? true });
    }
    
    if (options?.limit) {
      query = query.limit(options.limit);
    }
    
    if (options?.offset) {
      query = query.range(options.offset, options.offset + (options.limit || 10) - 1);
    }
    
    const { data, error } = await query;
    if (error) throw error;
    return data || [];
  },

  // Get single package by name
  get: async (packageName: string): Promise<Package | null> => {
    const { data, error } = await getSupabase()
      .from('packages')
      .select('*')
      .eq('name', packageName)
      .single();
    if (error) throw error;
    return data;
  },

  // Add or update package
  upsert: async (pkg: Package): Promise<Package> => {
    const { data, error } = await getSupabase()
      .from('packages')
      .upsert(pkg, { onConflict: 'name' })
      .select()
      .single();
    if (error) throw error;
    return data;
  },

  // Delete package
  delete: async (packageName: string): Promise<void> => {
    const { error } = await getSupabase()
      .from('packages')
      .delete()
      .eq('name', packageName);
    if (error) throw error;
  },

  // Search packages by keyword
  search: async (query: string): Promise<Package[]> => {
    const { data, error } = await getSupabase()
      .from('packages')
      .select('*')
      .or(`name.ilike.%${query}%,description.ilike.%${query}%`)
      .limit(50);
    if (error) throw error;
    return data || [];
  },

  // Update package stats
  updateStats: async (packageName: string, stats: Partial<Package>): Promise<void> => {
    const { error } = await getSupabase()
      .from('packages')
      .update(stats)
      .eq('name', packageName);
    if (error) throw error;
  },
};

// ============================================================================
// SAVED PACKAGES API
// ============================================================================

export const savedPackages = {
  getAll: async (): Promise<SavedPackage[]> => {
    const { data, error } = await getSupabase()
      .from('saved_packages')
      .select('*')
      .order('saved_at', { ascending: false });
    if (error) throw error;
    return data || [];
  },

  save: async (packageName: string, metadata?: Partial<SavedPackage>): Promise<void> => {
    const { error } = await getSupabase()
      .from('saved_packages')
      .upsert({
        package_name: packageName,
        ...metadata
      }, { onConflict: 'package_name' });
    if (error && error.code !== '23505') throw error;
  },

  remove: async (packageName: string): Promise<void> => {
    const { error } = await getSupabase()
      .from('saved_packages')
      .delete()
      .eq('package_name', packageName);
    if (error) throw error;
  },

  updateTags: async (packageName: string, tags: string[]): Promise<void> => {
    const { error } = await getSupabase()
      .from('saved_packages')
      .update({ tags })
      .eq('package_name', packageName);
    if (error) throw error;
  },

  toggleFavorite: async (packageName: string): Promise<void> => {
    const { data } = await getSupabase()
      .from('saved_packages')
      .select('favorite')
      .eq('package_name', packageName)
      .single();
    
    const { error } = await getSupabase()
      .from('saved_packages')
      .update({ favorite: !data?.favorite })
      .eq('package_name', packageName);
    if (error) throw error;
  },
};

// ============================================================================
// PACKAGE VERSIONS API
// ============================================================================

export const packageVersions = {
  getAll: async (packageName: string): Promise<PackageVersion[]> => {
    const { data, error } = await getSupabase()
      .from('package_versions')
      .select('*')
      .eq('package_name', packageName)
      .order('published_at', { ascending: false });
    if (error) throw error;
    return data || [];
  },

  getLatest: async (packageName: string): Promise<PackageVersion | null> => {
    const { data, error } = await getSupabase()
      .from('package_versions')
      .select('*')
      .eq('package_name', packageName)
      .eq('is_latest', true)
      .single();
    if (error) throw error;
    return data;
  },

  get: async (packageName: string, version: string): Promise<PackageVersion | null> => {
    const { data, error } = await getSupabase()
      .from('package_versions')
      .select('*')
      .eq('package_name', packageName)
      .eq('version', version)
      .single();
    if (error) throw error;
    return data;
  },

  upsert: async (version: PackageVersion): Promise<PackageVersion> => {
    const { data, error } = await getSupabase()
      .from('package_versions')
      .upsert(version, { onConflict: 'package_name,version' })
      .select()
      .single();
    if (error) throw error;
    return data;
  },

  markSynced: async (versionId: number): Promise<void> => {
    const { error } = await getSupabase()
      .from('package_versions')
      .update({
        contents_synced: true,
        synced_at: new Date().toISOString()
      })
      .eq('id', versionId);
    if (error) throw error;
  },
};

// ============================================================================
// PACKAGE ANALYSES API
// ============================================================================

export const packageAnalyses = {
  get: async (packageName: string): Promise<PackageAnalysis | null> => {
    const { data, error } = await getSupabase()
      .from('package_analyses')
      .select('*')
      .eq('package_name', packageName)
      .order('analyzed_at', { ascending: false })
      .limit(1)
      .single();
    if (error && error.code !== 'PGRST116') throw error;
    return data || null;
  },

  save: async (analysis: PackageAnalysis): Promise<PackageAnalysis> => {
    const { data, error } = await getSupabase()
      .from('package_analyses')
      .insert(analysis)
      .select()
      .single();
    if (error) throw error;
    return data;
  },

  getTopByMetric: async (metric: string, limit: number = 10): Promise<PackageAnalysis[]> => {
    const { data, error } = await getSupabase()
      .from('package_analyses')
      .select('*')
      .order(metric, { ascending: false })
      .limit(limit);
    if (error) throw error;
    return data || [];
  },
};

// ============================================================================
// DIRECTORY TREE API
// ============================================================================

export const directoryTree = {
  getForVersion: async (versionId: number): Promise<DirectoryEntry[]> => {
    const { data, error } = await getSupabase()
      .from('directory_tree')
      .select('*')
      .eq('version_id', versionId)
      .order('path');
    if (error) throw error;
    return data || [];
  },

  getRootEntries: async (versionId: number): Promise<DirectoryEntry[]> => {
    const { data, error } = await getSupabase()
      .from('directory_tree')
      .select('*')
      .eq('version_id', versionId)
      .eq('depth', 0)
      .order('name');
    if (error) throw error;
    return data || [];
  },

  getChildren: async (versionId: number, parentPath: string): Promise<DirectoryEntry[]> => {
    const { data, error } = await getSupabase()
      .from('directory_tree')
      .select('*')
      .eq('version_id', versionId)
      .eq('parent_path', parentPath)
      .order('type', { ascending: false }) // directories first
      .order('name');
    if (error) throw error;
    return data || [];
  },

  bulkInsert: async (entries: DirectoryEntry[]): Promise<void> => {
    const { error } = await getSupabase()
      .from('directory_tree')
      .upsert(entries, { onConflict: 'version_id,path' });
    if (error) throw error;
  },
};

// ============================================================================
// CODE FILES API
// ============================================================================

export const codeFiles = {
  getForVersion: async (versionId: number, options?: {
    includeContent?: boolean;
    fileType?: string;
    language?: string;
  }): Promise<CodeFile[]> => {
    let select = options?.includeContent ? '*' : '*, content:!inner()';
    let query = getSupabase()
      .from('code_files')
      .select(select)
      .eq('version_id', versionId);
    
    if (options?.fileType) {
      query = query.eq('file_type', options.fileType);
    }
    
    if (options?.language) {
      query = query.eq('language', options.language);
    }
    
    const { data, error } = await query.order('path');
    if (error) throw error;
    return data || [];
  },

  get: async (versionId: number, path: string): Promise<CodeFile | null> => {
    const { data, error } = await getSupabase()
      .from('code_files')
      .select('*')
      .eq('version_id', versionId)
      .eq('path', path)
      .single();
    if (error) throw error;
    return data;
  },

  getById: async (fileId: string): Promise<CodeFile | null> => {
    const { data, error } = await getSupabase()
      .from('code_files')
      .select('*')
      .eq('id', fileId)
      .single();
    if (error) throw error;
    return data;
  },

  bulkInsert: async (files: CodeFile[]): Promise<void> => {
    const { error } = await getSupabase()
      .from('code_files')
      .upsert(files, { onConflict: 'version_id,path' });
    if (error) throw error;
  },

  getEntryPoints: async (versionId: number): Promise<CodeFile[]> => {
    const { data, error } = await getSupabase()
      .from('code_files')
      .select('*')
      .eq('version_id', versionId)
      .eq('is_entry_point', true);
    if (error) throw error;
    return data || [];
  },

  searchContent: async (versionId: number, searchTerm: string): Promise<CodeFile[]> => {
    // FIX: The `textSearch` method breaks Supabase's automatic type inference. Using `.returns<CodeFile[]>()`
    // manually casts the response data to the correct type, resolving the compilation error.
    const { data, error } = await getSupabase()
      .from('code_files')
      .select('*')
      .eq('version_id', versionId)
      .textSearch('content', searchTerm, { type: 'websearch' })
      .limit(100)
      .returns<CodeFile[]>();
    if (error) throw error;
    return data || [];
  },
};

// ============================================================================
// PAST SEARCHES API
// ============================================================================

export const searches = {
  getAll: async (limit: number = 50): Promise<PastSearch[]> => {
    const { data, error } = await getSupabase()
      .from('past_searches')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(limit);
    if (error) throw error;
    return data || [];
  },

  get: async (searchId: string): Promise<PastSearch | null> => {
    const { data, error } = await getSupabase()
      .from('past_searches')
      .select('*')
      .eq('id', searchId)
      .single();
    if (error) throw error;
    return data;
  },

  save: async (search: PastSearch): Promise<void> => {
    const { error } = await getSupabase()
      .from('past_searches')
      .upsert(search, { onConflict: 'id' });
    if (error) throw error;
  },

  delete: async (searchId: string): Promise<void> => {
    const { error } = await getSupabase()
      .from('past_searches')
      .delete()
      .eq('id', searchId);
    if (error) throw error;
  },

  clearAll: async (): Promise<void> => {
    const { error } = await getSupabase()
      .from('past_searches')
      .delete()
      .neq('id', 'placeholder');
    if (error) throw error;
  },
};

// ============================================================================
// SYNC LOGIC
// ============================================================================

export const sync = {
    syncPackageContents: async (packageName: string): Promise<void> => {
        const fullPackageInfo = await getPackageInfo(packageName);
        if (!fullPackageInfo) throw new Error("Could not fetch full package info.");
        const latestVersionString = fullPackageInfo['dist-tags'].latest;
        const versionDetails = fullPackageInfo.versions[latestVersionString];
        if (!versionDetails) throw new Error(`Could not find details for latest version: ${latestVersionString}`);

        const versionForDb: PackageVersion = {
            package_name: packageName,
            version: latestVersionString,
            is_latest: true,
            tarball_url: versionDetails.dist.tarball,
            unpacked_size: versionDetails.dist.unpackedSize,
            file_count: versionDetails.dist.fileCount,
            dependencies: versionDetails.dependencies,
            dev_dependencies: versionDetails.devDependencies,
            peer_dependencies: versionDetails.peerDependencies,
            published_at: fullPackageInfo.time[latestVersionString],
        };
        const savedVersion = await packageVersions.upsert(versionForDb);
        const versionId = savedVersion.id;
        if (!versionId) throw new Error("Could not save package version");

        const fileTree = await getPackageFileTree(packageName, latestVersionString);
        const entries: DirectoryEntry[] = [];
        
        function traverse(node: FileNode, parentPath: string | undefined, depth: number) {
            const currentPath = node.path;
            const name = currentPath.split('/').pop() || '';
            
            entries.push({
                version_id: versionId!,
                path: currentPath,
                name: name,
                type: node.type,
                parent_path: parentPath,
                depth: depth,
                size_bytes: node.size,
            });
            if (node.type === 'directory' && node.files) {
                node.files.forEach(child => traverse(child, currentPath, depth + 1));
            }
        }
        
        if (fileTree.files) {
            fileTree.files.forEach(node => traverse(node, '/', 0));
        }
        
        if (entries.length > 0) {
            await directoryTree.bulkInsert(entries);
        }
        
        await packageVersions.markSynced(versionId);
        await packages.updateStats(packageName, { last_synced_at: new Date().toISOString() });
    }
};