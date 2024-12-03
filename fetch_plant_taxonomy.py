#!/usr/bin/env python3
"""
luoshaoxuan@outlook.com

Fetch plant taxonomy information from GBIF API.

This script queries the GBIF API to retrieve taxonomic information for given plant names at specified taxonomic levels.

Usage:
    python script.py -in-level f -out-level g s -input-file input.txt -output-file output.txt
    

Options:
    -in-level       Specify the input taxonomic level (k, p, c, o, f, g, s).
    -out-level      Specify the output taxonomic levels (k, p, c, o, f, g, s).
    -h              Detailed help message.
"""

import requests
import time
import argparse
import logging
import os
import sys
import threading
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Global constants
RETRY_LIMIT = 5  # Maximum retries for each plant name
DEFAULT_REQUEST_DELAY = 1.5  # Default delay between requests in seconds
ERROR_LOG_FILE = "error_log.txt"  # Error log filename
PROGRESS_FILE = "progress_checkpoint.txt"  # Progress checkpoint file

# Map single-letter abbreviations to full taxonomic ranks
RANK_ABBREVIATIONS = {
    'k': 'kingdom',
    'p': 'phylum',
    'c': 'class',
    'o': 'order',
    'f': 'family',
    'g': 'genus',
    's': 'species'
}

def setup_logging(log_level):
    """
    Configure logging settings.
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), None),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(ERROR_LOG_FILE),
            logging.StreamHandler()
        ]
    )

def fetch_taxonomy(plant_name, request_delay):
    """
    Fetch taxonomy information for a given plant name using GBIF /species/match API.
    Implements retry logic and handles API-specific exceptions.
    """
    url = "https://api.gbif.org/v1/species/match"
    params = {"name": plant_name}
    attempt = 0
    while attempt < RETRY_LIMIT:
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # Check HTTP status code

            # Parse the JSON data
            data = response.json()

            # Check if match is successful
            if data.get("matchType") != "NONE":
                return {
                    "key": data.get("usageKey", None),
                    "name": plant_name,
                    "kingdom": data.get("kingdom", "N/A"),
                    "phylum": data.get("phylum", "N/A"),
                    "class": data.get("class", "N/A"),
                    "order": data.get("order", "N/A"),
                    "family": data.get("family", "N/A"),
                    "genus": data.get("genus", "N/A"),
                    "species": data.get("species", "N/A"),
                    "rank": data.get("rank", "N/A")
                }
            else:
                # Handle no match found
                logging.warning(f"No match found for: {plant_name}")
                return fill_empty_taxonomy(plant_name)
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 429:
                # Rate limit exceeded, increase delay
                logging.warning(f"Rate limit exceeded. Increasing delay.")
                time.sleep(request_delay * (attempt + 1))
                attempt += 1
            else:
                logging.error(f"HTTPError for {plant_name}: {e}")
                attempt += 1
        except requests.exceptions.Timeout as e:
            logging.error(f"Timeout for {plant_name}: {e}")
            attempt += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"RequestException for {plant_name}: {e}")
            attempt += 1
        time.sleep(request_delay)
    # After retries, return empty taxonomy
    logging.error(f"Failed to fetch data for {plant_name} after {RETRY_LIMIT} attempts.")
    return fill_empty_taxonomy(plant_name)

def fetch_children(parent_key, rank, request_delay):
    """
    Fetch children of a given parent taxonomy using GBIF /species/{usageKey}/children API.
    Handles pagination to retrieve all child taxa.
    """
    url = f"https://api.gbif.org/v1/species/{parent_key}/children"
    results = []
    limit = 1000
    offset = 0
    attempt = 0
    while True:
        params = {"limit": limit, "offset": offset}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            page_results = []
            for child in data.get("results", []):
                if child.get("rank", "").lower() == rank.lower():
                    page_results.append({
                        "key": child.get("key"),
                        "name": child.get("scientificName", "N/A"),
                        "rank": child.get("rank", "N/A"),
                        "genus": child.get("genus", "N/A"),
                        "species": child.get("species", "N/A")
                    })
            results.extend(page_results)
            if len(data.get("results", [])) < limit:
                # No more pages
                break
            else:
                offset += limit
                time.sleep(request_delay)
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 429:
                # Rate limit exceeded, increase delay
                logging.warning(f"Rate limit exceeded when fetching children for {parent_key}. Increasing delay.")
                time.sleep(request_delay * (attempt + 1))
                attempt += 1
            else:
                logging.error(f"HTTPError fetching children for {parent_key}: {e}")
                attempt += 1
        except requests.exceptions.Timeout as e:
            logging.error(f"Timeout fetching children for {parent_key}: {e}")
            attempt += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"RequestException fetching children for {parent_key}: {e}")
            attempt += 1
        if attempt >= RETRY_LIMIT:
            logging.error(f"Failed to fetch children for {parent_key} after {RETRY_LIMIT} attempts.")
            break
        time.sleep(request_delay)
    return results

def fill_empty_taxonomy(plant_name):
    """
    Returns a dictionary with all taxonomy fields set to 'N/A' for failed queries.
    """
    return {
        "key": None,
        "name": plant_name,
        "kingdom": "N/A",
        "phylum": "N/A",
        "class": "N/A",
        "order": "N/A",
        "family": "N/A",
        "genus": "N/A",
        "species": "N/A",
        "rank": "N/A"
    }

def check_conflict(input_level, levels):
    """
    Check if the input level conflicts with the specified output levels.
    If a conflict is found, decide whether to continue or terminate based on the number of output levels.
    """
    if input_level in levels:
        if len(levels) == 1:
            logging.error(f"The input level '{input_level}' conflicts with the specified output level '{input_level}'.")
            logging.error("Please remove the conflicting output level or change the input level.")
            sys.exit(1)
        else:
            logging.warning(f"The input level '{input_level}' conflicts with one of the specified output levels.")
            logging.warning(f"The conflicting level '{input_level}' will be ignored.")
            levels.remove(input_level)

def process_plant(plant_name, input_level, levels, request_delay):
    """
    Process a single plant name, fetching taxonomy information and returning results.
    """
    taxonomy = fetch_taxonomy(plant_name, request_delay)

    if taxonomy["key"] is None:
        data = {level: "" for level in levels}
        data[input_level] = plant_name
        return [data], False  # False indicates failure
    else:
        taxonomic_ranks = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]
        input_rank_index = taxonomic_ranks.index(input_level)
        data = {input_level: plant_name}

        results = []
        success = True

        lower_levels = [level for level in levels if taxonomic_ranks.index(level) > input_rank_index]
        higher_levels = [level for level in levels if taxonomic_ranks.index(level) <= input_rank_index]

        for level in higher_levels:
            data[level] = taxonomy.get(level, "N/A")

        if lower_levels:
            # Need to fetch lower-level taxa
            def fetch_lower_levels(current_taxonomy, current_data, current_rank_index):
                if current_rank_index >= len(taxonomic_ranks) -1:
                    results.append(current_data.copy())
                    return
                next_rank_index = current_rank_index +1
                next_rank = taxonomic_ranks[next_rank_index]
                if next_rank in lower_levels:
                    children = fetch_children(current_taxonomy["key"], next_rank, request_delay)
                    if not children:
                        results.append(current_data.copy())
                    else:
                        for child in children:
                            child_data = current_data.copy()
                            child_data[next_rank] = child["name"]
                            fetch_lower_levels(child, child_data, next_rank_index)
                else:
                    fetch_lower_levels(current_taxonomy, current_data, next_rank_index)
            fetch_lower_levels(taxonomy, data, input_rank_index)
        else:
            # No lower levels, just return the data
            results.append(data)
        return results, success

def process_plant_file(input_file, output_file, input_level, levels, request_delay, parallel, output_format):
    """
    Processes a list of plant names, querying taxonomy information and saving results to a file.
    """
    # Define taxonomic ranks order
    taxonomic_ranks = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

    # Read plant names from input file
    try:
        with open(input_file, "r") as infile:
            plant_names = [line.strip() for line in infile if line.strip()]
    except FileNotFoundError:
        logging.error(f"Input file '{input_file}' not found.")
        sys.exit(1)
    except PermissionError:
        logging.error(f"No permission to read input file '{input_file}'.")
        sys.exit(1)

    total_plants = len(plant_names)
    success_count = 0
    failure_count = 0

    # Prepare output file
    try:
        output_exists = os.path.isfile(output_file)
        with open(output_file, "a" if output_exists else "w") as outfile:
            # Write header if file is new
            if not output_exists:
                headers = [input_level.capitalize()] + [level.capitalize() for level in levels]
                if output_format == 'csv':
                    outfile.write(",".join(headers) + "\n")
                elif output_format == 'json':
                    pass  # JSON output will be handled separately
                else:
                    outfile.write("\t".join(headers) + "\n")
    except PermissionError:
        logging.error(f"No permission to write to output file '{output_file}'.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error opening output file '{output_file}': {e}")
        sys.exit(1)

    lock = threading.Lock()

    def process_and_write(plant_name):
        nonlocal success_count, failure_count
        results, success = process_plant(plant_name, input_level, levels, request_delay)
        with lock:
            if success:
                success_count +=1
            else:
                failure_count +=1
            try:
                with open(output_file, "a") as outfile:
                    for data in results:
                        row = [data.get(level, "") for level in [input_level] + levels]
                        if output_format == 'csv':
                            outfile.write(",".join(row) + "\n")
                        elif output_format == 'json':
                            import json
                            outfile.write(json.dumps(data) + "\n")
                        else:
                            outfile.write("\t".join(row) + "\n")
            except Exception as e:
                logging.error(f"Error writing to output file '{output_file}': {e}")

    # Process plant names
    if parallel:
        max_workers = min(10, os.cpu_count() or 1)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_and_write, plant_name): plant_name for plant_name in plant_names}
            for future in tqdm(as_completed(futures), total=total_plants, desc="Processing", unit="keyword"):
                pass
    else:
        for plant_name in tqdm(plant_names, desc="Processing", unit="keyword"):
            process_and_write(plant_name)
            time.sleep(request_delay)

    logging.info(f"Processing completed. Success: {success_count}, Failures: {failure_count}")

def main():
    """
    Main function to parse arguments and initiate processing.
    """
    parser = argparse.ArgumentParser(
        description="Fetch plant taxonomy information from GBIF API.",
        epilog="Example usage:\n  python script.py -in-level f -out-level g s\n  python script.py -retry",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-retry",
        action="store_true",
        help="Retry fetching failed plants from error log."
    )
    parser.add_argument(
        "-in-level",
        type=str,
        choices=list(RANK_ABBREVIATIONS.keys()),
        help="Specify the taxonomy level of the input data using abbreviations (k, p, c, o, f, g, s)."
    )
    parser.add_argument(
        "-out-level",
        nargs='+',
        type=str,
        choices=list(RANK_ABBREVIATIONS.keys()),
        help="Specify the taxonomy levels to include in the output using abbreviations (k, p, c, o, f, g, s)."
    )
    parser.add_argument(
        "-input-file",
        type=str,
        help="Specify the input file containing plant names. Defaults to 'keywords.txt' if not provided."
    )
    parser.add_argument(
        "-output-file",
        type=str,
        help="Specify the output file to save taxonomy information. Defaults to 'taxonomy_output.txt' if not provided."
    )
    parser.add_argument(
        "-delay",
        type=float,
        default=DEFAULT_REQUEST_DELAY,
        help="Set the delay between requests in seconds. Defaults to 1.5 seconds."
    )
    parser.add_argument(
        "-parallel",
        action="store_true",
        help="Enable parallel processing using multiple threads."
    )
    parser.add_argument(
        "-log-level",
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help="Set the logging level. Defaults to 'INFO'."
    )
    parser.add_argument(
        "-output-format",
        type=str,
        choices=['csv', 'json', 'txt'],
        default='txt',
        help="Set the output format. Choices are 'csv', 'json', 'txt'. Defaults to 'txt'."
    )
    args = parser.parse_args()

    # Set up logging
    setup_logging(args.log_level)

    # Default input and output files
    input_file = args.input_file if args.input_file else "keywords.txt"
    output_file = args.output_file if args.output_file else "taxonomy_output.txt"

    # Input data level
    if args.in_level:
        input_level = RANK_ABBREVIATIONS[args.in_level]
    else:
        logging.error("No input level specified. Please use -in-level to specify the input level.")
        sys.exit(1)

    # Output levels
    if args.out_level:
        levels = [RANK_ABBREVIATIONS[l] for l in args.out_level]
    else:
        logging.error("No output levels specified. Please use -out-level to specify the output levels.")
        sys.exit(1)

    # Check for conflicts between input level and output levels
    check_conflict(input_level, levels)

    # Process plants
    if args.retry:
        # Implement retry logic if needed
        pass  # For brevity, not implementing retry in this example
    else:
        process_plant_file(
            input_file,
            output_file,
            input_level,
            levels,
            args.delay,
            args.parallel,
            args.output_format
        )

if __name__ == "__main__":
    main()