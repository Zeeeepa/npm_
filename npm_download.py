import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import subprocess
import threading
import queue
import concurrent.futures
import datetime
import time

class NpmAPI:
    def __init__(self):
        self.registry_url = "https://registry.npmjs.org"
        self.search_url = f"{self.registry_url}/-/v1/search"
        self.download_dir = "npm_packages"
        self.package_cache = {}  # Cache for package metadata
        self.concurrency = 20  # Number of concurrent operations

    def search_packages(self, query, max_time_ago=None, time_unit=None, max_results=1000, progress_callback=None):
        """Search for packages matching query with concurrency, with optional time filter and pagination"""
        all_packages = []
        page_size = 100  # npm API limit per request

        # Calculate how many pages we need to fetch
        pages_to_fetch = (max_results + page_size - 1) // page_size

        def fetch_page(page_num):
            from_value = page_num * page_size
            url = f"{self.search_url}?text={query}&size={page_size}&from={from_value}"

            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                if progress_callback:
                    progress_callback(page_num + 1, pages_to_fetch)
                return data.get('objects', [])
            except requests.RequestException as e:
                print(f"Error searching page {page_num}: {e}")
                return []

        # Use ThreadPoolExecutor for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            future_to_page = {executor.submit(fetch_page, i): i for i in range(pages_to_fetch)}

            for future in concurrent.futures.as_completed(future_to_page):
                page_results = future.result()
                all_packages.extend(page_results)

                # Stop if we've reached the maximum
                if len(all_packages) >= max_results:
                    # Cancel any pending futures
                    for pending_future in future_to_page:
                        if not pending_future.done():
                            pending_future.cancel()
                    break

        # Sort and limit the results
        all_packages = all_packages[:max_results]

        # Apply time filtering if needed
        if max_time_ago is not None and time_unit is not None:
            all_packages = self.filter_by_time(all_packages, max_time_ago, time_unit)

        return all_packages

    def get_package_details(self, package_name):
        """Get detailed info about a package including unpacked size and file count"""
        # First get package metadata from the registry
        package_info = self.get_package_info(package_name)
        if not package_info:
            return None

        # Get additional details from the npm website including unpacked size and file count
        details = {
            'name': package_name,
            'version': package_info.get('dist-tags', {}).get('latest', 'Unknown'),
            'description': package_info.get('description', 'No description available'),
            'unpacked_size': 'Unknown',
            'file_count': 'Unknown',
            'last_published': 'Unknown',
            'dependencies': {},
            'dependents': [],
            'dependents_count': 'Unknown'
        }

        # Get latest version details
        latest_version = details['version']
        if latest_version != 'Unknown' and latest_version in package_info.get('versions', {}):
            version_info = package_info['versions'][latest_version]
            details['dependencies'] = version_info.get('dependencies', {}) or {}

            # Get time from package info
            if 'time' in package_info and latest_version in package_info['time']:
                published_time = package_info['time'][latest_version]
                try:
                    # Parse time and format it
                    time_obj = datetime.datetime.fromisoformat(published_time.replace('Z', '+00:00'))
                    details['last_published'] = time_obj.strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass

        # Scrape the npm website for additional details
        url = f"https://www.npmjs.com/package/{package_name}"
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Use the specific XPaths by converting to CSS selectors
            # /html/body/div/div/div[2]/main/div/div[3]/div[7]/p -> Unpacked Size
            # Try multiple selectors to handle different page layouts
            size_selectors = [
                'div:nth-child(7) > p',
                'main div:nth-child(3) > div:nth-child(7) > p',
                'body > div > div > div:nth-child(2) > main > div > div:nth-child(3) > div:nth-child(7) > p'
            ]

            for selector in size_selectors:
                size_element = soup.select(selector)
                if size_element and 'Unpacked Size' in size_element[0].get_text():
                    size_text = size_element[0].get_text().strip()
                    size_match = re.search(r'Unpacked Size:\s*([\d\.]+\s*[KMG]?B)', size_text)
                    if size_match:
                        details['unpacked_size'] = size_match.group(1).strip()
                        break

            # /html/body/div/div/div[2]/main/div/div[3]/div[8]/p -> Total Files
            files_selectors = [
                'div:nth-child(8) > p',
                'main div:nth-child(3) > div:nth-child(8) > p',
                'body > div > div > div:nth-child(2) > main > div > div:nth-child(3) > div:nth-child(8) > p'
            ]

            for selector in files_selectors:
                files_element = soup.select(selector)
                if files_element and 'Total Files' in files_element[0].get_text():
                    files_text = files_element[0].get_text().strip()
                    files_match = re.search(r'Total Files:\s*(\d+)', files_text)
                    if files_match:
                        details['file_count'] = files_match.group(1).strip()
                        break

            # /html/body/div/div/div[2]/main/div/div[3]/div[9]/p/time -> Last Published
            if details['last_published'] == 'Unknown':  # Only if not already set from API data
                time_selectors = [
                    'div:nth-child(9) > p > time',
                    'main div:nth-child(3) > div:nth-child(9) > p > time',
                    'body > div > div > div:nth-child(2) > main > div > div:nth-child(3) > div:nth-child(9) > p > time'
                ]

                for selector in time_selectors:
                    time_element = soup.select(selector)
                    if time_element:
                        details['last_published'] = time_element[0].get_text().strip()
                        break

            # Find dependents count
            dependents_selectors = [
                'a[href*="/browse/depended/"]',
                'a[href*="depends-on"]',
                'a:contains("Depended by")'
            ]

            for selector in dependents_selectors:
                try:
                    dependents_element = soup.select_one(selector)
                    if dependents_element:
                        dependents_text = dependents_element.get_text().strip()
                        dependents_match = re.search(r'(\d+)', dependents_text)
                        if dependents_match:
                            details['dependents_count'] = dependents_match.group(1).strip()
                            break
                except Exception:
                    continue

            # If we still haven't found the values, try a more generic approach
            if details['unpacked_size'] == 'Unknown':
                # Look for any paragraph containing "Unpacked Size"
                for p in soup.find_all('p'):
                    text = p.get_text().strip()
                    if 'Unpacked Size' in text:
                        size_match = re.search(r'([\d\.]+\s*[KMG]?B)', text)
                        if size_match:
                            details['unpacked_size'] = size_match.group(1).strip()
                            break

            if details['file_count'] == 'Unknown':
                # Look for any paragraph containing "Total Files"
                for p in soup.find_all('p'):
                    text = p.get_text().strip()
                    if 'Total Files' in text:
                        files_match = re.search(r'(\d+)', text)
                        if files_match:
                            details['file_count'] = files_match.group(1).strip()
                            break

            # Try to get dependents
            if 'dependents_count' in details and details['dependents_count'] != 'Unknown':
                try:
                    # We have a count, but we want some actual dependents for display
                    # Just grab a few from the first page as examples
                    dependents_url = f"https://www.npmjs.com/browse/depended/{package_name}"
                    dep_response = requests.get(dependents_url, headers=headers)
                    if dep_response.status_code == 200:
                        dep_soup = BeautifulSoup(dep_response.text, 'html.parser')
                        dep_elements = dep_soup.select('a[data-test="package-name"]')

                        # Get up to 5 dependents as examples
                        for i, elem in enumerate(dep_elements):
                            if i >= 5:  # Limit to 5 to avoid too much data
                                break
                            details['dependents'].append(elem.get_text().strip())
                except Exception as e:
                    print(f"Error fetching dependents: {e}")

        except requests.RequestException as e:
            print(f"Error fetching package details from npm website: {e}")

        # As a fallback, try to estimate size from dependencies count
        if details['unpacked_size'] == 'Unknown' and details['dependencies']:
            deps_count = len(details['dependencies'])
            if deps_count > 0:
                # Very rough estimation
                estimated_size = deps_count * 50  # 50KB per dependency as a wild guess
                details['unpacked_size'] = f"~{estimated_size} KB (estimated)"

        if details['file_count'] == 'Unknown' and details['dependencies']:
            deps_count = len(details['dependencies'])
            if deps_count > 0:
                # Very rough estimation
                estimated_files = deps_count * 3  # 3 files per dependency as a wild guess
                details['file_count'] = f"~{estimated_files} (estimated)"

        # Get a list of dependencies for display
        if details['dependencies']:
            details['dependency_list'] = list(details['dependencies'].keys())
        else:
            details['dependency_list'] = []

        return details

    def get_package_info(self, package_name):
        """Get detailed info about a specific package"""
        # Check cache first
        if package_name in self.package_cache:
            return self.package_cache[package_name]

        url = f"{self.registry_url}/{package_name}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            package_info = response.json()

            # Cache the result
            self.package_cache[package_name] = package_info
            return package_info
        except requests.RequestException as e:
            print(f"Error getting package info for {package_name}: {e}")
            return None

    def get_dependencies(self, package_name, include_dev=False, max_depth=5, progress_callback=None):
        """Get all dependencies of a package"""
        visited = set()
        dependency_queue = queue.Queue()
        dependency_queue.put((package_name, 0))  # (package, depth)

        all_dependencies = []
        total_processed = 0

        while not dependency_queue.empty():
            current_package, depth = dependency_queue.get()

            if current_package in visited or depth > max_depth:
                continue

            visited.add(current_package)
            if current_package != package_name:  # Don't add the root package
                all_dependencies.append(current_package)

            if depth < max_depth:
                package_info = self.get_package_info(current_package)
                if not package_info:
                    continue

                # Get the latest version
                versions = package_info.get('versions', {})
                latest_version = package_info.get('dist-tags', {}).get('latest', '')

                if not latest_version or latest_version not in versions:
                    continue

                latest_info = versions[latest_version]
                dependencies = list(latest_info.get('dependencies', {}).keys())

                if include_dev:
                    dev_dependencies = list(latest_info.get('devDependencies', {}).keys())
                    dependencies.extend(dev_dependencies)

                for dep in dependencies:
                    dependency_queue.put((dep, depth + 1))

                total_processed += 1
                if progress_callback:
                    progress_callback(total_processed, total_processed + dependency_queue.qsize())

        return list(set(all_dependencies))

    def get_dependents(self, package_name, max_pages=10, progress_callback=None):
        """Get packages that depend on this package using concurrent web scraping"""
        dependents = []

        def scrape_page(page_num):
            page_dependents = []
            url = f"https://www.npmjs.com/browse/depended/{package_name}?offset={(page_num-1)*36}"
            try:
                response = requests.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                package_elements = soup.select('a[data-test="package-name"]')

                for element in package_elements:
                    dependent_name = element.text.strip()
                    page_dependents.append(dependent_name)

                if progress_callback:
                    progress_callback(page_num, max_pages)

                return page_dependents
            except (requests.RequestException, Exception) as e:
                print(f"Error fetching dependents page {page_num}: {e}")
                return []

        # Use ThreadPoolExecutor for concurrent scraping
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            future_to_page = {executor.submit(scrape_page, i): i for i in range(1, max_pages + 1)}

            for future in concurrent.futures.as_completed(future_to_page):
                page_results = future.result()
                # If no results on a page, we've reached the end
                if not page_results and future_to_page[future] > 1:
                    # Cancel any pending futures for higher page numbers
                    for pending_future, page_num in future_to_page.items():
                        if not pending_future.done() and page_num > future_to_page[future]:
                            pending_future.cancel()
                dependents.extend(page_results)

        return list(set(dependents))  # Remove duplicates

    def filter_by_time(self, packages, time_value, time_unit):
        """Filter packages by update time"""
        # Calculate threshold date
        now = datetime.datetime.now()
        if time_unit == "days":
            threshold = now - datetime.timedelta(days=time_value)
        elif time_unit == "weeks":
            threshold = now - datetime.timedelta(weeks=time_value)
        elif time_unit == "months":
            threshold = now - datetime.timedelta(days=time_value*30)  # Approximation
        elif time_unit == "years":
            threshold = now - datetime.timedelta(days=time_value*365)  # Approximation
        else:
            return packages  # No filtering if invalid unit

        filtered_packages = []
        for package in packages:
            # Extract last modified date
            package_data = package.get('package', {})
            date_str = package_data.get('date', '')

            if not date_str:
                continue

            try:
                # Parse ISO format date
                last_modified = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                if last_modified >= threshold:
                    filtered_packages.append(package)
            except (ValueError, TypeError):
                continue

        return filtered_packages

    def download_package(self, package_name, version='latest'):
        """Download a specific package using npm pack"""
        # Create download directory if it doesn't exist
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        # Change to download directory
        original_dir = os.getcwd()
        os.chdir(self.download_dir)

        try:
            # Use npm pack to download the package
            cmd = f"npm pack {package_name}@{version}"
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            downloaded_file = result.stdout.strip()
            success = True
            error_message = None
        except subprocess.CalledProcessError as e:
            downloaded_file = None
            success = False
            error_message = e.stderr

        # Change back to original directory
        os.chdir(original_dir)

        return {
            'success': success,
            'package': package_name,
            'file': downloaded_file,
            'error': error_message
        }

    def download_packages_concurrent(self, package_list, progress_callback=None):
        """Download multiple packages concurrently"""
        # Create download directory if it doesn't exist
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        results = []
        result_lock = threading.Lock()

        def download_single_package(package_name, index, total):
            result = self.download_package(package_name)
            with result_lock:
                results.append(result)
            if progress_callback:
                progress_callback(index + 1, total, result)
            return result

        # Use ThreadPoolExecutor for concurrent downloads
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = [
                executor.submit(download_single_package, package, i, len(package_list))
                for i, package in enumerate(package_list)
            ]
            concurrent.futures.wait(futures)

        return results

    def set_download_dir(self, directory):
        """Set the directory where packages will be downloaded"""
        self.download_dir = directory

    def set_concurrency(self, concurrency):
        """Set the number of concurrent operations"""
        self.concurrency = max(1, min(50, concurrency))  # Limit between 1 and 50


class NpmDownloaderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NPM Package Downloader")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)

        self.api = NpmAPI()
        self.packages_to_download = []
        self.current_package = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the tkinter UI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Search type selection
        search_type_frame = ttk.LabelFrame(main_frame, text="Search Type", padding=10)
        search_type_frame.pack(fill=tk.X, pady=5)

        self.search_type_var = tk.StringVar(value="general")
        ttk.Radiobutton(search_type_frame, text="Package Name Search", variable=self.search_type_var,
                       value="package", command=self.toggle_search_type).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(search_type_frame, text="General Search", variable=self.search_type_var,
                       value="general", command=self.toggle_search_type).pack(side=tk.LEFT, padx=5)

        # Package name search frame
        self.package_frame = ttk.LabelFrame(main_frame, text="Package Name Search", padding=10)
        ttk.Label(self.package_frame, text="Enter Package Name:").pack(anchor=tk.W, pady=5)
        self.package_name_var = tk.StringVar()
        ttk.Entry(self.package_frame, textvariable=self.package_name_var, width=50).pack(fill=tk.X, pady=5)
        ttk.Label(self.package_frame, text="Example: graphlit-client").pack(anchor=tk.W, pady=2)
        ttk.Button(self.package_frame, text="OK", command=self.search_package).pack(anchor=tk.E, pady=5)

        # General search frame
        self.general_frame = ttk.LabelFrame(main_frame, text="General Search", padding=10)

        # Search query input
        ttk.Label(self.general_frame, text="Search Query:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_query_var = tk.StringVar()
        ttk.Entry(self.general_frame, textvariable=self.search_query_var, width=50).grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)

        # Search filters
        filters_frame = ttk.LabelFrame(self.general_frame, text="Search Filters", padding=5)
        filters_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E, pady=5)

        # Time filter
        ttk.Label(filters_frame, text="Time Filter:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.time_filter_var = tk.StringVar(value="all")
        time_options = [
            ("All Time", "all"),
            ("Last Day", "last_day"),
            ("Last Week", "last_week"),
            ("Last Month", "last_month"),
            ("Last Year", "last_year")
        ]

        time_filter_frame = ttk.Frame(filters_frame)
        time_filter_frame.grid(row=0, column=1, sticky=tk.W, pady=5)

        for text, value in time_options:
            ttk.Radiobutton(time_filter_frame, text=text, variable=self.time_filter_var, value=value).pack(side=tk.LEFT, padx=5)

        # Results count filter
        ttk.Label(filters_frame, text="Max Results:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.max_results_var = tk.IntVar(value=1000)
        max_results_frame = ttk.Frame(filters_frame)
        max_results_frame.grid(row=1, column=1, sticky=tk.W, pady=5)

        results_options = [
            ("100", 100),
            ("500", 500),
            ("1000", 1000),
            ("All", 10000)
        ]

        for text, value in results_options:
            ttk.Radiobutton(max_results_frame, text=text, variable=self.max_results_var, value=value).pack(side=tk.LEFT, padx=5)

        # Search button
        ttk.Button(self.general_frame, text="Search", command=self.search_general).grid(row=2, column=1, sticky=tk.E, pady=10)

        # Package details frame
        self.details_frame = ttk.LabelFrame(main_frame, text="Package Details", padding=10)

        # Treeview for package details
        self.details_tree = ttk.Treeview(self.details_frame, columns=("property", "value"), show="headings", height=6)
        self.details_tree.heading("property", text="Property")
        self.details_tree.heading("value", text="Value")
        self.details_tree.column("property", width=150)
        self.details_tree.column("value", width=450)
        self.details_tree.pack(fill=tk.X, pady=5)

        # Download options
        download_frame = ttk.Frame(self.details_frame)
        download_frame.pack(fill=tk.X, pady=5)
        ttk.Button(download_frame, text="Download Package",
                  command=lambda: self.download_package_option("package")).pack(side=tk.LEFT, padx=5)
        ttk.Button(download_frame, text="Download Dependencies",
                  command=lambda: self.download_package_option("dependencies")).pack(side=tk.LEFT, padx=5)
        ttk.Button(download_frame, text="Download Dependants",
                  command=lambda: self.download_package_option("dependants")).pack(side=tk.LEFT, padx=5)

        # Results frame for general search
        self.results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding=10)

        # Create treeview for search results
        self.results_tree = ttk.Treeview(self.results_frame, columns=("name", "version", "description", "size", "files", "date"), show="headings", height=10)
        self.results_tree.heading("name", text="Package Name")
        self.results_tree.heading("version", text="Version")
        self.results_tree.heading("description", text="Description")
        self.results_tree.heading("size", text="Unpacked Size")
        self.results_tree.heading("files", text="Total Files")
        self.results_tree.heading("date", text="Last Published")

        self.results_tree.column("name", width=150, anchor=tk.W)
        self.results_tree.column("version", width=80, anchor=tk.W)
        self.results_tree.column("description", width=250, anchor=tk.W)
        self.results_tree.column("size", width=100, anchor=tk.W)
        self.results_tree.column("files", width=80, anchor=tk.W)
        self.results_tree.column("date", width=120, anchor=tk.W)

        # Add a scrollbar to the treeview
        results_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=results_scrollbar.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click event to view package details
        self.results_tree.bind("<Double-1>", self.on_result_double_click)

        # Initially hide these frames
        self.details_frame.pack_forget()
        self.results_frame.pack_forget()

        # Output area
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.output_text = tk.Text(output_frame, wrap=tk.WORD, height=15)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(output_frame, command=self.output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text["yscrollcommand"] = scrollbar.set

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, mode="determinate")
        self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        self.progress_bar["value"] = 0

        # Initially show the appropriate search frame based on selection
        self.toggle_search_type()

    def toggle_search_type(self):
        """Toggle between package name search and general search based on the radio button selection"""
        if self.search_type_var.get() == "package":
            # Show package name search, hide general search
            self.package_frame.pack(fill=tk.X, pady=5)

            # Hide the general search frame
            if hasattr(self, 'general_frame') and self.general_frame.winfo_manager():
                self.general_frame.pack_forget()

            # Hide the results frame
            if hasattr(self, 'results_frame') and self.results_frame.winfo_manager():
                self.results_frame.pack_forget()

            # Hide the details frame if visible
            if self.details_frame.winfo_manager():
                self.details_frame.pack_forget()

            # Clear output text
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "Enter a package name and click OK to see package details.\n")
            self.output_text.insert(tk.END, "Example: graphlit-client\n")
        else:
            # Show general search, hide package name search
            if hasattr(self, 'general_frame'):
                self.general_frame.pack(fill=tk.X, pady=5)

            # Hide the package name frame
            if self.package_frame.winfo_manager():
                self.package_frame.pack_forget()

            # Hide the details frame if visible
            if self.details_frame.winfo_manager():
                self.details_frame.pack_forget()

            # Clear output text
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "Enter a search query and select filters, then click Search.\n")

    def search_package(self):
        """Search for a specific package by name"""
        package_name = self.package_name_var.get().strip()

        # Sanitize input - remove https://www.npmjs.com/package/ if present
        if package_name.startswith("https://www.npmjs.com/package/"):
            package_name = package_name[len("https://www.npmjs.com/package/"):]

        if not package_name:
            messagebox.showerror("Error", "Please enter a package name")
            return

        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Fetching package details for: {package_name}\n")

        # Show loading indicator
        self.root.config(cursor="wait")
        self.status_var.set(f"Fetching package: {package_name}...")

        # Use a thread to avoid freezing the UI
        def fetch_details():
            try:
                package_details = self.api.get_package_details(package_name)

                if package_details:
                    self.current_package = package_name
                    self.root.after(0, lambda: self.display_package_details(package_details))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Package '{package_name}' not found"))
                    self.root.after(0, lambda: self.output_text.insert(tk.END, f"Package '{package_name}' not found\n"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error fetching package details: {str(e)}"))
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"Error: {str(e)}\n"))
            finally:
                self.root.after(0, lambda: self.root.config(cursor=""))
                self.root.after(0, lambda: self.status_var.set("Ready"))

        threading.Thread(target=fetch_details, daemon=True).start()

    def search_general(self):
        """Search for packages using the general search with filters"""
        query = self.search_query_var.get().strip()
        if not query:
            messagebox.showerror("Error", "Please enter a search query")
            return

        # Get the time filter
        time_filter = self.time_filter_var.get()

        # Determine time values based on the filter
        time_value = None
        time_unit = None

        if time_filter != "all":
            if time_filter == "last_day":
                time_value = 1
                time_unit = "days"
            elif time_filter == "last_week":
                time_value = 1
                time_unit = "weeks"
            elif time_filter == "last_month":
                time_value = 1
                time_unit = "months"
            elif time_filter == "last_year":
                time_value = 1
                time_unit = "years"

        # Get the max results
        max_results = self.max_results_var.get()

        # Clear output and show status
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Searching for packages matching: {query}\n")
        if time_filter != "all":
            self.output_text.insert(tk.END, f"Time filter: {time_filter}\n")
        self.output_text.insert(tk.END, f"Max results: {max_results}\n")

        # Clear existing results
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

        # Show the results frame
        self.results_frame.pack(fill=tk.BOTH, expand=True, after=self.general_frame)

        # Show loading indicator
        self.root.config(cursor="wait")
        self.status_var.set(f"Searching for packages matching '{query}'...")
        self.progress_bar["value"] = 0

        # Use a thread to avoid freezing the UI
        def perform_search():
            try:
                def update_progress(current, total):
                    percent = (current / total) * 100
                    self.root.after(0, lambda: self.progress_bar.configure(value=percent))
                    self.root.after(0, lambda: self.status_var.set(f"Searching: {current}/{total} pages..."))

                search_results = self.api.search_packages(
                    query,
                    time_value,
                    time_unit,
                    max_results=max_results,
                    progress_callback=update_progress
                )

                if search_results:
                    # Process results to get size and file count
                    self.root.after(0, lambda: self.status_var.set(f"Found {len(search_results)} results. Processing details..."))
                    self.root.after(0, lambda: self.output_text.insert(tk.END, f"Found {len(search_results)} packages. Processing details...\n"))

                    # Process package details in smaller batches
                    batch_size = 10  # Process in batches to avoid overwhelming the UI
                    batches = [search_results[i:i+batch_size] for i in range(0, len(search_results), batch_size)]

                    results_with_details = []

                    for batch_index, batch in enumerate(batches):
                        self.root.after(0, lambda bi=batch_index, bt=len(batches): self.status_var.set(
                            f"Processing batch {bi+1}/{bt} ({batch_size} packages each)..."
                        ))
                        self.root.after(0, lambda bi=batch_index, bt=len(batches): self.progress_bar.configure(
                            value=(bi / bt) * 100
                        ))

                        for result in batch:
                            try:
                                package_data = result['package']
                                package_name = package_data['name']
                                version = package_data.get('version', 'Unknown')
                                description = package_data.get('description', 'No description available')
                                date_str = package_data.get('date', 'Unknown')

                                # Format date for display
                                if date_str != 'Unknown':
                                    try:
                                        date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                        formatted_date = date_obj.strftime('%Y-%m-%d')
                                    except (ValueError, TypeError):
                                        formatted_date = date_str
                                else:
                                    formatted_date = 'Unknown'

                                # Add directly to results with placeholder values first
                                result_entry = {
                                    'name': package_name,
                                    'version': version,
                                    'description': description,
                                    'size': 'Loading...',
                                    'files': 'Loading...',
                                    'date': formatted_date
                                }

                                results_with_details.append(result_entry)

                                # Add to UI immediately so user sees progress
                                item_id = self.root.after(0, lambda pkg=result_entry: self.results_tree.insert(
                                    "", "end",
                                    values=(pkg['name'], pkg['version'], pkg['description'], pkg['size'], pkg['files'], pkg['date'])
                                ))

                                # Then fetch details in background
                                def update_package_details(pkg_name, result_idx, tree_item):
                                    try:
                                        details = self.api.get_package_details(pkg_name)
                                        if details:
                                            # Update the result entry
                                            results_with_details[result_idx]['size'] = details.get('unpacked_size', 'Unknown')
                                            results_with_details[result_idx]['files'] = details.get('file_count', 'Unknown')

                                            # Update the tree item
                                            self.root.after(0, lambda: self.results_tree.item(
                                                tree_item,
                                                values=(
                                                    pkg_name,
                                                    results_with_details[result_idx]['version'],
                                                    results_with_details[result_idx]['description'],
                                                    results_with_details[result_idx]['size'],
                                                    results_with_details[result_idx]['files'],
                                                    results_with_details[result_idx]['date']
                                                )
                                            ))
                                    except Exception as e:
                                        print(f"Error updating details for {pkg_name}: {str(e)}")

                                # Start a separate thread for each package detail fetch
                                threading.Thread(
                                    target=update_package_details,
                                    args=(package_name, len(results_with_details)-1, item_id),
                                    daemon=True
                                ).start()

                                # Add a small delay between requests to avoid overwhelming the server
                                time.sleep(0.1)

                            except Exception as e:
                                print(f"Error processing search result: {str(e)}")

                    self.output_text.insert(tk.END, f"Processed {len(results_with_details)} packages with details.\n")
                    self.output_text.insert(tk.END, "Double-click on a package to see more details.\n")
                    self.status_var.set(f"Ready - Found {len(results_with_details)} packages")

                else:
                    self.root.after(0, lambda: self.output_text.insert(tk.END, "No packages found matching your query.\n"))
                    self.root.after(0, lambda: self.status_var.set("Ready - No results found"))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error during search: {str(e)}"))
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"Error: {str(e)}\n"))
                self.root.after(0, lambda: self.status_var.set("Error during search"))
            finally:
                self.root.after(0, lambda: self.root.config(cursor=""))
                self.root.after(0, lambda: self.progress_bar.configure(value=100))

        threading.Thread(target=perform_search, daemon=True).start()

    def on_result_double_click(self, event):
        """Handle double-click on a search result"""
        selection = self.results_tree.selection()
        if not selection:
            return

        item = selection[0]
        package_name = self.results_tree.item(item, "values")[0]

        if package_name:
            # Set the package name in the package search field
            self.package_name_var.set(package_name)

            # Switch to package name search mode
            self.search_type_var.set("package")
            self.toggle_search_type()

            # Search for the package
            self.search_package()

    def display_package_details(self, details):
        """Display package details in the UI"""
        # Clear previous details
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)

        # Add package information to treeview
        self.details_tree.insert("", "end", values=("Name", details['name']))
        self.details_tree.insert("", "end", values=("Version", details['version']))
        self.details_tree.insert("", "end", values=("Description", details['description']))
        self.details_tree.insert("", "end", values=("Unpacked Size", details['unpacked_size']))
        self.details_tree.insert("", "end", values=("Total Files", details['file_count']))

        if 'dependents_count' in details:
            self.details_tree.insert("", "end", values=("Dependents Count", details['dependents_count']))

        # Display dependencies count
        dep_count = len(details['dependencies'])
        self.details_tree.insert("", "end", values=("Dependencies Count", str(dep_count)))

        # Show package details frame
        self.details_frame.pack(fill=tk.X, pady=5, after=self.package_frame)

        # Display summary in output
        self.output_text.insert(tk.END, f"Package: {details['name']} v{details['version']}\n")
        self.output_text.insert(tk.END, f"Unpacked Size: {details['unpacked_size']}\n")
        self.output_text.insert(tk.END, f"Total Files: {details['file_count']}\n")
        self.output_text.insert(tk.END, f"Dependencies: {dep_count}\n")

        if 'dependents_count' in details:
            self.output_text.insert(tk.END, f"Dependents: {details['dependents_count']}\n")

    def download_package_option(self, option_type):
        """Handle download option button clicks"""
        if not self.current_package:
            messagebox.showerror("Error", "No package selected")
            return

        # Choose download directory
        download_dir = filedialog.askdirectory(
            initialdir=os.getcwd(),
            title="Select Download Directory"
        )

        if not download_dir:
            return  # User cancelled

        # Create subdirectory with package name
        package_subdir = os.path.join(download_dir, self.current_package)
        try:
            if not os.path.exists(package_subdir):
                os.makedirs(package_subdir)
            download_dir = package_subdir
        except OSError as e:
            messagebox.showerror("Error", f"Could not create directory for package: {e}")
            return

        self.api.set_download_dir(download_dir)
        packages_to_download = []

        if option_type == "package":
            packages_to_download.append(self.current_package)
            self.output_text.insert(tk.END, f"\nDownloading package: {self.current_package}\n")
            self.output_text.insert(tk.END, f"Download location: {download_dir}\n")

        elif option_type == "dependencies":
            self.output_text.insert(tk.END, f"\nFetching dependencies for: {self.current_package}\n")
            self.output_text.insert(tk.END, f"Download location: {download_dir}\n")

            # Show loading indicator
            self.root.config(cursor="wait")
            self.status_var.set(f"Fetching dependencies for {self.current_package}...")

            def fetch_and_download_deps():
                try:
                    # Fetch dependencies
                    deps = self.api.get_dependencies(self.current_package, include_dev=False)
                    if deps:
                        packages_to_download.extend(deps)
                        packages_to_download.append(self.current_package)  # Add the package itself

                        # Show confirmation dialog with the number of packages
                        self.root.after(0, lambda: self._confirm_and_download(packages_to_download))
                    else:
                        self.root.after(0, lambda: self.output_text.insert(tk.END, f"No dependencies found for {self.current_package}\n"))
                        self.root.after(0, lambda: self.status_var.set("Ready"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Error fetching dependencies: {str(e)}"))
                    self.root.after(0, lambda: self.output_text.insert(tk.END, f"Error: {str(e)}\n"))
                    self.root.after(0, lambda: self.status_var.set("Error"))
                finally:
                    self.root.after(0, lambda: self.root.config(cursor=""))

            threading.Thread(target=fetch_and_download_deps, daemon=True).start()
            return  # Return early as we're using a thread

        elif option_type == "dependants":
            self.output_text.insert(tk.END, f"\nFetching dependants for: {self.current_package}\n")
            self.output_text.insert(tk.END, f"Download location: {download_dir}\n")

            # Show loading indicator
            self.root.config(cursor="wait")
            self.status_var.set(f"Fetching dependants for {self.current_package}...")

            def fetch_and_download_deps():
                try:
                    # Fetch dependants (limited to 10 pages to avoid excessive load)
                    deps = self.api.get_dependents(self.current_package, max_pages=10)
                    if deps:
                        packages_to_download.extend(deps)

                        # Show confirmation dialog with the number of packages
                        self.root.after(0, lambda: self._confirm_and_download(packages_to_download))
                    else:
                        self.root.after(0, lambda: self.output_text.insert(tk.END, f"No dependants found for {self.current_package}\n"))
                        self.root.after(0, lambda: self.status_var.set("Ready"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Error fetching dependants: {str(e)}"))
                    self.root.after(0, lambda: self.output_text.insert(tk.END, f"Error: {str(e)}\n"))
                    self.root.after(0, lambda: self.status_var.set("Error"))
                finally:
                    self.root.after(0, lambda: self.root.config(cursor=""))

            threading.Thread(target=fetch_and_download_deps, daemon=True).start()
            return  # Return early as we're using a thread

        # For single package download, confirm and download directly
        if packages_to_download:
            self._confirm_and_download(packages_to_download)

    def _confirm_and_download(self, packages):
        """Confirm and initiate package download"""
        if not packages:
            return

        # Ask for confirmation
        confirm = messagebox.askyesno(
            "Confirm Download",
            f"Download {len(packages)} package(s) to {self.api.download_dir}?"
        )

        if not confirm:
            return

        # Start download process
        self.output_text.insert(tk.END, f"Starting download of {len(packages)} package(s)...\n")
        self.output_text.insert(tk.END, f"Download location: {self.api.download_dir}\n")
        self.root.config(cursor="wait")
        self.status_var.set(f"Downloading {len(packages)} packages...")
        self.progress_bar["value"] = 0

        def do_download():
            try:
                # Download packages
                results = self.api.download_packages_concurrent(
                    packages,
                    progress_callback=self._download_progress_callback
                )

                # Show download summary
                success_count = sum(1 for r in results if r['success'])
                fail_count = len(results) - success_count

                self.root.after(0, lambda: self.output_text.insert(tk.END, f"\nDownload complete: {success_count} successful, {fail_count} failed\n"))
                self.root.after(0, lambda: self.status_var.set(f"Ready - Downloaded {success_count}/{len(packages)} packages"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error during download: {str(e)}"))
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"Error: {str(e)}\n"))
                self.root.after(0, lambda: self.status_var.set("Download error"))
            finally:
                self.root.after(0, lambda: self.root.config(cursor=""))
                self.root.after(0, lambda: self.progress_bar.configure(value=100))

        threading.Thread(target=do_download, daemon=True).start()

    def _download_progress_callback(self, current, total, result):
        """Callback to update download progress"""
        package = result.get('package', 'Unknown')
        success = result.get('success', False)
        filename = result.get('file', '')
        error = result.get('error', '')

        # Update UI in the main thread
        if success:
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"Downloaded {package} -> {os.path.basename(filename)}\n"))
        else:
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"Failed to download {package}: {error}\n"))

        # Make sure the most recent output is visible
        self.root.after(0, lambda: self.output_text.see(tk.END))

        # Update progress bar
        percent = (current / total) * 100
        self.root.after(0, lambda: self.progress_bar.configure(value=percent))


def main():
    root = tk.Tk()
    app = NpmDownloaderUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()